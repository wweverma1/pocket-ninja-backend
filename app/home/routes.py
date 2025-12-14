from flask import Blueprint

from app.home.controller import home

home_endpoints = Blueprint('home', __name__)

home_endpoints.add_url_rule(rule='/', view_func=home, methods=['GET'])