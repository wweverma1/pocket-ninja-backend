import os

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

from app.home.routes import home_endpoints
from app.product.routes import product_endpoints

app.register_blueprint(home_endpoints)
app.register_blueprint(product_endpoints)

from app.utils.app_functions import (
    before_request,
    after_request,
)