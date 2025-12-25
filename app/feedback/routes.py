from flask import Blueprint

from app.feedback.controller import (
    get_avg_rating,
    submit_feedback
)

feedback_endpoints = Blueprint('feedback', __name__, url_prefix="/feedback")

feedback_endpoints.add_url_rule(rule='/', view_func=get_avg_rating, methods=['GET'])
feedback_endpoints.add_url_rule(rule='/', view_func=submit_feedback, methods=['PUT'])
