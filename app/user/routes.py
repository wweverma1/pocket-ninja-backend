from flask import Blueprint

from app.user.controller import (
    onboard_user
)

user_endpoints = Blueprint('user', __name__, url_prefix="/user")

user_endpoints.add_url_rule(rule='/onboard', view_func=onboard_user, methods=['POST'])
