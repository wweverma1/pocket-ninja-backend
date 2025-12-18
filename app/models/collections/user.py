from app.database.db import db 
from datetime import datetime, timezone
from bson.objectid import ObjectId

class User:
    """
    Model class to handle database operations for the 'users' collection.
    
    Collection Key Properties:
    _id (ObjectId), username (unique), googleAccountId, lineAccountId, yahooAccountId, 
    totalContributions, rankScore, hostRating (totalPoints, totalRatings), 
    totalExpenditure, estimatedTotalSavings, joinedAt.
    """
    
    @staticmethod
    def get_collection():
        """Helper to get the MongoDB collection or None if DB is not ready."""
        if db is None:
            return None
        return db['users']

    @staticmethod
    def create_user(username: str, line_account_id: str = None, google_account_id: str = None, yahoo_account_id: str = None):
        """
        Creates a new user document.
        """
        collection = User.get_collection()

        # FIX APPLIED PREVIOUSLY: Use explicit 'is None' check
        if collection is None: 
            return None
        
        user_data = {
            "username": username,
            "totalContributions": 0,
            "rankScore": 0,
            "hostRating": {"totalPoints": 0, "totalRatings": 0},
            "totalExpenditure": 0.0,
            "estimatedTotalSavings": 0.0,
            "joinedAt": datetime.now(timezone.utc)
        }
        
        # FIX APPLIED: Conditionally add social IDs only if they are NOT None.
        # This ensures the field is MISSING from the document if not provided.
        if line_account_id is not None:
            user_data["lineAccountId"] = line_account_id
        if google_account_id is not None:
            user_data["googleAccountId"] = google_account_id
        if yahoo_account_id is not None:
            user_data["yahooAccountId"] = yahoo_account_id
        
        try:
            # Enforce uniqueness on username
            collection.create_index([("username", 1)], unique=True)

            # FIX APPLIED: Use the simple $exists: true filter.
            # This is safe now because we omit the field if the value is None.
            
            # Enforce uniqueness on external social IDs (only if present)
            if "lineAccountId" in user_data:
                collection.create_index([("lineAccountId", 1)], unique=True, partialFilterExpression={"lineAccountId": {"$exists": True}})
            if "googleAccountId" in user_data:
                collection.create_index([("googleAccountId", 1)], unique=True, partialFilterExpression={"googleAccountId": {"$exists": True}})
            if "yahooAccountId" in user_data:
                collection.create_index([("yahooAccountId", 1)], unique=True, partialFilterExpression={"yahooAccountId": {"$exists": True}})
                
            result = collection.insert_one(user_data)
            return result.inserted_id
        except Exception as e:
            # Handle potential duplicate key error (username or social ID conflict)
            print(f"Error creating user: {e}")
            return None

    @staticmethod
    def get_id_and_username_by_social_account_id(social_id: str, provider: str):
        """
        Retrieves a user's MongoDB ObjectId (_id) by their social media ID and provider.
        """
        collection = User.get_collection()
        if collection is None:
            return None
            
        field_map = {
            'google': 'googleAccountId',
            'line': 'lineAccountId',
            'yahoo': 'yahooAccountId'
        }
        
        field = field_map.get(provider)
        if not field:
            return None

        # Project only the _id field for efficiency
        user = collection.find_one({field: social_id}, {"_id": 1})
        return (user['_id'], user['username']) if user else (None, None)

    @staticmethod
    def get_by_id(user_id: str):
        """
        Retrieves a user document by its MongoDB ObjectId.
        """
        collection = User.get_collection()
        if collection is None or not ObjectId.is_valid(user_id):
            return None
        
        return collection.find_one({"_id": ObjectId(user_id)})

    @staticmethod
    def update_username(user_id: str, chosen_username: str):
        """
        Sets the username and returns a status code:
        0: Success
        1: Username already taken by someone else
        2: Database/Connection error
        """
        collection = User.get_collection()
        if collection is None or not ObjectId.is_valid(user_id):
            return 2

        # 1. Check if the username is already taken by ANYONE else
        # We exclude the current user from this check so they can "re-save" their own name
        existing_user = collection.find_one({
            "username": chosen_username,
            "_id": {"$ne": ObjectId(user_id)}
        })
        
        if existing_user:
            return 1

        # 2. Update the user regardless of whether they already had a username
        result = collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"username": chosen_username}}
        )

        if result.matched_count == 0:
            # User ID not found in database
            return 2

        return 0
    
    @staticmethod
    def update_estimated_savings(user_id: str, savings_amount: float):
        """
        Updates the user's estimatedTotalSavings using the MongoDB ObjectId.
        """
        collection = User.get_collection()
        if collection is None or not ObjectId.is_valid(user_id):
            return False
        
        result = collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"estimatedTotalSavings": savings_amount}} 
        )
        return result.modified_count == 1