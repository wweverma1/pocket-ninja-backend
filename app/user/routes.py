from flask import Blueprint

from app.user.controller import (
    get_profile, 
    update_username
)

user_endpoints = Blueprint('user', __name__, url_prefix="/user")

user_endpoints.add_url_rule(rule='/', view_func=get_profile, methods=['GET'])
user_endpoints.add_url_rule(rule='/', view_func=update_username, methods=['POST'])

