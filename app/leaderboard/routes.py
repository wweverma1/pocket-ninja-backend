from flask import Blueprint

from app.leaderboard.controller import get_leaderboard

leaderboard_endpoints = Blueprint('leaderboard', __name__, url_prefix="/leaderboard")

leaderboard_endpoints.add_url_rule(rule='/', view_func=get_leaderboard, methods=['GET'])