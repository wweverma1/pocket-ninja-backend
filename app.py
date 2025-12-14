import os

from dotenv import load_dotenv
load_dotenv()

from app import app

debug = os.getenv("DEBUG")

if __name__ == "__main__":
    app.run(
        host='0.0.0.0', 
        port=5000, 
        debug=(True if debug == "true" else False)
    )