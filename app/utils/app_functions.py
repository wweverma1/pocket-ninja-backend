import time

from datetime import datetime
from flask import request, make_response
from app import app


@app.before_request
def before_request():
    # 1. Handle Preflight OPTIONS requests immediately
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response, 200

    request.start_time = time.time()


@app.after_request
def after_request(response):
    # 2. Add CORS headers to all successful requests
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'

    # 3. Logging (only if it wasn't an OPTIONS request)
    if request.method != 'OPTIONS' and request.endpoint:
        end_time = time.time()
        latency = int((end_time - request.start_time) * 1000)
        print(f'[ {str(datetime.now())} ] endpoint {request.endpoint} latency {latency}ms')
        
    return response
