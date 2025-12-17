from flask import request, jsonify
from app.models.collections.user import User
from app.utils.auth_helper import token_required
from app.models.response import Response


@token_required
def onboard_user(current_user):
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
        status = User.assign_username(user_id, chosen_username)

        if status == 0:
            # Success
            result = {"username": chosen_username}
            response = Response(
                errorStatus=0,
                message_en="Onboarding successful!",
                message_jp="オンボーディングが完了しました！",
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

        elif status == 2:
            # Username already set
            response = Response(
                message_en="Username has already been set and cannot be changed.",
                message_jp="ユーザー名は既に設定されており、変更できません。"
            )
            return jsonify(response.to_dict()), 403

        else:
            # DB Error or Status 3
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
