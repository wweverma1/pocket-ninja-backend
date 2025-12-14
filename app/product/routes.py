from flask import Blueprint

from app.home.controller import (
    add_or_update_product_details,
    get_product_details
)

product_endpoints = Blueprint('product', __name__)

product_endpoints.add_url_rule(rule='/product/details', view_func=add_or_update_product_details, methods=['PUT'])
product_endpoints.add_url_rule(rule='/product/details', view_func=get_product_details, methods=['GET'])