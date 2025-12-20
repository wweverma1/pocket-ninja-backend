from flask import Blueprint

from app.product.controller import (
    add_or_update_product_details,
    get_product_details
)

product_endpoints = Blueprint('product', __name__, url_prefix="/product")

product_endpoints.add_url_rule(
    rule='/', view_func=add_or_update_product_details, methods=['PUT'])
product_endpoints.add_url_rule(
    rule='/', view_func=get_product_details, methods=['GET'])
