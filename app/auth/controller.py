import os
import requests
from flask import request, redirect, url_for, jsonify
from app.models.response import Response
from app.models.collections.user import User
from app.utils.auth_helper import encode_auth_token
from bson.objectid import ObjectId

# Configuration from environment variables
BASE_URL = os.getenv("BASE_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")

# --- Helper function for Final Redirect ---

def final_redirect(token: str, is_new_user: bool, error_message: str = None):
    """Redirects the user back to the frontend with the token or an error."""
    if error_message:
        return redirect(f"{FRONTEND_URL}/auth/failure?error={error_message}")
        
    # Redirect to frontend success page, passing the JWT and new user status
    return redirect(f"{FRONTEND_URL}/auth/success?token={token}&is_new_user={is_new_user}")

# --- Phase 1: Initiation Functions (Redirect to Provider) ---

def google_redirect():
    """Constructs the Google OAuth URL and redirects the user."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = f"{BASE_URL}/auth/callback/google"
    
    # Google's base authorization endpoint
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile', # Requesting basic profile info
        'state': 'pocket-ninja-state' # CSRF protection (basic)
    }
    
    import urllib.parse
    auth_url_with_params = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url_with_params)

def line_redirect():
    """Constructs the LINE OAuth URL and redirects the user."""
    client_id = os.getenv("LINE_CHANNEL_ID")
    redirect_uri = f"{BASE_URL}/auth/callback/line"
    
    # LINE's base authorization endpoint
    AUTH_URL = "https://access.line.me/oauth2/v2.1/authorize"
    
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'profile openid', # Required scope for getting basic user info
        'state': 'pocket-ninja-line-state' # CSRF protection
    }
    
    import urllib.parse
    auth_url_with_params = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url_with_params)

def yahoo_redirect():
    """Constructs the Yahoo OAuth URL and redirects the user."""
    client_id = os.getenv("YAHOO_CLIENT_ID")
    redirect_uri = f"{BASE_URL}/auth/callback/yahoo"
    
    # Yahoo's base authorization endpoint
    AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
    
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'openid profile', # Requesting basic profile info
        'state': 'pocket-ninja-yahoo-state' # CSRF protection
    }
    
    import urllib.parse
    auth_url_with_params = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url_with_params)

# --- Phase 2: Callback Functions (Provider sends code, backend exchanges it) ---

def google_callback():
    """Receives the authorization code and exchanges it for a token/profile."""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return final_redirect(None, False, f"Provider error: {error}")
        
    if not code:
        return final_redirect(None, False, "Authorization code missing")
        
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = f"{BASE_URL}/auth/callback/google"
    
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
    
    # 1. Exchange code for tokens
    token_exchange_payload = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        token_response = requests.post(TOKEN_URL, data=token_exchange_payload)
        token_response.raise_for_status() # Raise exception for bad status codes
        access_token = token_response.json().get('access_token')
        
        if not access_token:
            return final_redirect(None, False, "Failed to get access token from Google")
            
        # 2. Use Access Token to get User Profile (needed for social ID)
        userinfo_response = requests.get(USERINFO_URL, headers={'Authorization': f'Bearer {access_token}'})
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()
        
        social_id = user_info.get('sub') # 'sub' is the unique Google ID
        
        if not social_id:
             return final_redirect(None, False, "Failed to get unique social ID")

        # 3. Pocket Ninja Login/Signup Logic
        user_id_obj = User.get_id_by_social_account_id(social_id=social_id, provider='google')
        is_new_user = False
        
        if user_id_obj:
            # Existing User (Login)
            user_id_str = str(user_id_obj)
        else:
            # New User (Sign-up)
            is_new_user = True
            
            # NOTE: Placeholder username creation (as discussed previously)
            placeholder_username = f"ninja-google-{social_id[:4]}"
            
            new_user_id_obj = User.create_user(
                username=placeholder_username,
                google_account_id=social_id
            )
            
            if not new_user_id_obj:
                return final_redirect(None, False, "User registration failed")
                
            user_id_str = str(new_user_id_obj)

        # 4. Generate JWT Token
        token = encode_auth_token(user_id_str)
        
        # 5. Redirect back to frontend with the JWT
        return final_redirect(token, is_new_user)

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request Error during Google OAuth: {e}")
        return final_redirect(None, False, "Authentication server error")
    except Exception as e:
        print(f"Internal Error during Google OAuth: {e}")
        return final_redirect(None, False, "Internal server error")

def line_callback():
    """Receives the LINE authorization code and exchanges it for a token/profile."""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return final_redirect(None, False, f"Provider error: {error}")
        
    if not code:
        return final_redirect(None, False, "Authorization code missing")
        
    client_id = os.getenv("LINE_CHANNEL_ID")
    client_secret = os.getenv("LINE_CHANNEL_SECRET")
    redirect_uri = f"{BASE_URL}/auth/callback/line"
    
    TOKEN_URL = "https://api.line.me/oauth2/v2.1/token"
    PROFILE_URL = "https://api.line.me/v2/profile"
    
    # 1. Exchange code for tokens
    token_exchange_payload = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        token_response = requests.post(
            TOKEN_URL, 
            data=token_exchange_payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        token_response.raise_for_status()
        access_token = token_response.json().get('access_token')
        
        if not access_token:
            return final_redirect(None, False, "Failed to get access token from LINE")
            
        # 2. Use Access Token to get User Profile (needed for social ID)
        # The LINE user ID is stored in the 'userId' field from the profile endpoint
        profile_response = requests.get(
            PROFILE_URL, 
            headers={'Authorization': f'Bearer {access_token}'}
        )
        profile_response.raise_for_status()
        user_info = profile_response.json()
        
        social_id = user_info.get('userId') # LINE's unique ID field
        
        if not social_id:
             return final_redirect(None, False, "Failed to get unique social ID from LINE")

        # 3. Pocket Ninja Login/Signup Logic
        user_id_obj = User.get_id_by_social_account_id(social_id=social_id, provider='line')
        is_new_user = False
        
        if user_id_obj:
            # Existing User (Login)
            user_id_str = str(user_id_obj)
        else:
            # New User (Sign-up)
            is_new_user = True
            
            # NOTE: Placeholder username creation
            placeholder_username = f"ninja-line-{social_id[:4]}"
            
            new_user_id_obj = User.create_user(
                username=placeholder_username,
                line_account_id=social_id # Use the correct argument name
            )
            
            if not new_user_id_obj:
                return final_redirect(None, False, "User registration failed")
                
            user_id_str = str(new_user_id_obj)

        # 4. Generate JWT Token
        token = encode_auth_token(user_id_str)
        
        # 5. Redirect back to frontend with the JWT
        return final_redirect(token, is_new_user)

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request Error during LINE OAuth: {e}")
        return final_redirect(None, False, "Authentication server error")
    except Exception as e:
        print(f"Internal Error during LINE OAuth: {e}")
        return final_redirect(None, False, "Internal server error")

def yahoo_callback():
    """Receives the Yahoo authorization code and exchanges it for a token/profile."""
    code = request.args.get('code')
    error = request.args.get('error')
    
    if error:
        return final_redirect(None, False, f"Provider error: {error}")
        
    if not code:
        return final_redirect(None, False, "Authorization code missing")
        
    client_id = os.getenv("YAHOO_CLIENT_ID")
    client_secret = os.getenv("YAHOO_CLIENT_SECRET")
    redirect_uri = f"{BASE_URL}/auth/callback/yahoo"
    
    TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
    USERINFO_URL = "https://api.login.yahoo.com/openid/v1/userinfo"
    
    # 1. Exchange code for tokens
    token_exchange_payload = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }
    
    try:
        token_response = requests.post(
            TOKEN_URL, 
            data=token_exchange_payload,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        token_response.raise_for_status() 
        access_token = token_response.json().get('access_token')
        
        if not access_token:
            return final_redirect(None, False, "Failed to get access token from Yahoo")
            
        # 2. Use Access Token to get User Profile (needed for social ID)
        userinfo_response = requests.get(
            USERINFO_URL, 
            headers={'Authorization': f'Bearer {access_token}'}
        )
        userinfo_response.raise_for_status()
        user_info = userinfo_response.json()
        
        social_id = user_info.get('sub') # 'sub' is the unique Yahoo ID (as per OpenID Connect standard)
        
        if not social_id:
             return final_redirect(None, False, "Failed to get unique social ID from Yahoo")

        # 3. Pocket Ninja Login/Signup Logic
        user_id_obj = User.get_id_by_social_account_id(social_id=social_id, provider='yahoo')
        is_new_user = False
        
        if user_id_obj:
            # Existing User (Login)
            user_id_str = str(user_id_obj)
        else:
            # New User (Sign-up)
            is_new_user = True
            
            # NOTE: Placeholder username creation
            placeholder_username = f"ninja-yahoo-{social_id[:4]}"
            
            new_user_id_obj = User.create_user(
                username=placeholder_username,
                yahoo_account_id=social_id # Use the correct argument name
            )
            
            if not new_user_id_obj:
                return final_redirect(None, False, "User registration failed")
                
            user_id_str = str(new_user_id_obj)

        # 4. Generate JWT Token
        token = encode_auth_token(user_id_str)
        
        # 5. Redirect back to frontend with the JWT
        return final_redirect(token, is_new_user)

    except requests.exceptions.RequestException as e:
        print(f"HTTP Request Error during Yahoo OAuth: {e}")
        return final_redirect(None, False, "Authentication server error")
    except Exception as e:
        print(f"Internal Error during Yahoo OAuth: {e}")
        return final_redirect(None, False, "Internal server error")