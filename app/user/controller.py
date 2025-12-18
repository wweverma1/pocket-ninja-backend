from flask import request, jsonify
from app.models.collections.user import User
from app.utils.auth_helper import token_required
from app.models.response import Response

@token_required
def get_profile(current_user):
    """
    Retrieves the authenticated user's profile data with calculated ratings 
    and current month stats.
    """
    try:
        # Ensure monthly stats are fresh before returning
        User.check_and_reset_monthly_stats(str(current_user['_id']))
        
        # Calculate Average Rating (Base 5.0 + contributions)
        rating_obj = current_user.get('userRating', {})
        total_score = rating_obj.get('totalScore', 5.0)
        raters_count = len(rating_obj.get('ratedByUsers', []))
        
        # Average = total / (raters + 1 for the base rating)
        avg_rating = round(total_score / (raters_count + 1), 2)

        profile_data = {
            "username": current_user.get('username'),
            "joinedAt": current_user.get('joinedAt'),
            "rankScore": current_user.get('rankScore', 0),
            "lastRankIncrement": current_user.get('lastRankIncrement', 0),
            "totalContributions": current_user.get('totalContributions', 0),
            "totalExpenditure": current_user.get('totalExpenditure', 0.0),
            "estimatedTotalSavings": current_user.get('estimatedTotalSavings', 0.0),
            "userRating": avg_rating,
            "monthlyStats": {
                "month": current_user.get('statsMonth'),
                "contributions": current_user.get('monthlyContributions', 0),
                "expenditure": current_user.get('monthlyExpenditure', 0.0),
                "savings": current_user.get('monthlySavings', 0.0)
            }
        }

        response = Response(
            errorStatus=0,
            message_en="Profile retrieved successfully.",
            message_jp="プロフィールが正常に取得されました。",
            result=profile_data
        )
        return jsonify(response.to_dict()), 200

    except Exception as e:
        print(f"Profile Retrieval Error: {e}")
        response = Response(
            message_en="Failed to retrieve profile.",
            message_jp="プロフィールの取得に失敗しました。"
        )
        return jsonify(response.to_dict()), 500
    
@token_required
def update_username(current_user):
    try:
        data = request.get_json()
        if not data:
            response = Response(
                message_en="No input data provided.",
                message_jp="入力データがありません。"
            )
            return jsonify(response.to_dict()), 400

        chosen_username = data.get('username', '').strip()

        # 1. Validation: Length check
        if len(chosen_username) < 3:
            response = Response(
                message_en="Username must be at least 3 characters long.",
                message_jp="ユーザー名は3文字以上である必要があります。"
            )
            return jsonify(response.to_dict()), 400

        user_id = str(current_user['_id'])
        status = User.update_username(user_id, chosen_username)

        if status == 0:
            # Success
            result = {"username": chosen_username}
            response = Response(
                errorStatus=0,
                message_en="Username updated successfully!",
                message_jp="ユーザー名が正常に更新されました。",
                result=result
            )
            return jsonify(response.to_dict()), 200

        elif status == 1:
            # Username taken
            response = Response(
                message_en="This username is already taken. Please try another.",
                message_jp="このユーザー名は既に使用されています。別の名前を試してください。"
            )
            return jsonify(response.to_dict()), 409

        else:
            # DB Error or Status 2
            response = Response(
                message_en="Internal database error. Please try again later.",
                message_jp="データベースエラーが発生しました。後でもう一度お試しください。"
            )
            return jsonify(response.to_dict()), 500

    except Exception as e:
        print(f"Onboarding Error: {e}")
        response = Response(
            message_en="Internal server error during onboarding.",
            message_jp="オンボーディング中にサーバーエラーが発生しました。"
        )
        return jsonify(response.to_dict()), 500