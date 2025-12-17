from app.utils.app_functions import (
    before_request,
    after_request,
)
from app.product.routes import product_endpoints
from app.auth.routes import auth_endpoints
from app.home.routes import home_endpoints
from app.database.db import init_db
from dotenv import load_dotenv
import os

from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

load_dotenv()

init_db()


app.register_blueprint(home_endpoints)
app.register_blueprint(auth_endpoints)
app.register_blueprint(product_endpoints)
