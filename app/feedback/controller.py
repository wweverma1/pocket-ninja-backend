from flask import request, jsonify
from app.models.collections.feedback import Feedback
from app.utils.auth_helper import token_required, token_optional
from app.models.response import Response


@token_optional
def get_avg_rating(current_user):
    """
    GET /feedback
    Returns the average rating of the app.
    If authorized, also returns the user's previously submitted rating.
    """
    try:
        # 1. Get Global Average
        avg = Feedback.get_avg_rating()
        result_data = {"averageRating": avg}

        # 2. If User is Logged In, fetch their personal rating
        if current_user:
            user_id = str(current_user['_id'])
            user_feedback = Feedback.get_by_user_id(user_id)
            if user_feedback:
                result_data["userRating"] = user_feedback.get('rating', None)
            else:
                result_data["userRating"] = None

        response = Response(
            errorStatus=0,
            message_en="Average rating fetched successfully.",
            message_jp="平均評価が正常に取得されました。",
            result=result_data
        )
        return jsonify(response.to_dict()), 200
    except Exception as e:
        print(f"Error fetching avg rating: {e}")
        return jsonify(Response(message_en="Internal server error.", message_jp="内部サーバーエラー。").to_dict()), 500


@token_required
def submit_feedback(current_user):
    """
    PUT /feedback
    Accepts (optional): { "rating": int (1-5), "feedback": str }
    """
    try:
        data = request.get_json() or {}
        
        rating = data.get('rating')
        raw_message = data.get('feedback')
        
        # Prepare clean message (handle None or whitespace-only)
        clean_message = raw_message.strip() if raw_message else None

        # --- Validation 1: At least one field required ---
        if rating is None and not clean_message:
            response = Response(
                message_en="Please provide either a rating or feedback message.",
                message_jp="評価またはフィードバックメッセージのいずれかを提供してください。"
            )
            return jsonify(response.to_dict()), 400

        # --- Validation 2: Rating Validity (if provided) ---
        if rating is not None:
            if not isinstance(rating, int) or not (1 <= rating <= 5):
                response = Response(
                    message_en="Rating must be an integer between 1 and 5.",
                    message_jp="rating は 1 から 5 までの整数である必要があります。"
                )
                return jsonify(response.to_dict()), 400

        user_id = str(current_user['_id'])
        
        # Call upsert logic
        result = Feedback.upsert_feedback(user_id, rating, clean_message)

        if result:
            response = Response(
                errorStatus=0,
                message_en="Feedback submitted successfully!",
                message_jp="フィードバックが正常に送信されました！"
            )
            return jsonify(response.to_dict()), 200
        else:
            return jsonify(Response(message_en="Failed to save feedback.", message_jp="フィードバックの保存に失敗しました。").to_dict()), 500

    except Exception as e:
        print(f"Feedback Error: {e}")
        return jsonify(Response(message_en="Internal server error.", message_jp="内部サーバーエラー。").to_dict()), 500