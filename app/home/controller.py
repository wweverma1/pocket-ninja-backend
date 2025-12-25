from flask import (
    jsonify
)
from app.models.response import Response


def home():
    response = Response(errorStatus=0, message_en="⚡Pocket Ninja", message_ja="⚡Pocket Ninja")
    return jsonify(response.to_dict()), 200
