from flask import (
    jsonify
)
from app.models.response import Response


def home():
    response = Response(message="⚡Pocket Ninja")
    return jsonify(response.to_dict()), 200
