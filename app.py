import os

from app import app
from dotenv import load_dotenv

load_dotenv()

environment = os.getenv("ENVIRONMENT")

if __name__ == "__main__":
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=(True if environment == "debug" else False)
    )