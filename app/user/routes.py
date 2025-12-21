from flask import Blueprint

from app.user.controller import (
    get_profile,
    update_username,
    update_avatar_id,
    update_proximity,
    get_submitted_receipts
)

user_endpoints = Blueprint('user', __name__, url_prefix="/user")

user_endpoints.add_url_rule(rule='/', view_func=get_profile, methods=['GET'])
user_endpoints.add_url_rule(rule='/username', view_func=update_username, methods=['PUT'])
user_endpoints.add_url_rule(rule='/avatar/id', view_func=update_avatar_id, methods=['PUT'])
user_endpoints.add_url_rule(rule='/proximity', view_func=update_proximity, methods=['PUT'])
user_endpoints.add_url_rule(rule='/receipt', view_func=get_submitted_receipts, methods=['GET'])
