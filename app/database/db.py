import os
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Define the project's canonical database name based on the specification
DB_NAME = "pocket-ninja-db" 

# Global database client and object
client = None
db = None

def init_db():
    """
    Initializes the MongoDB connection.
    Variables are retrieved inside the function to ensure they are loaded 
    after load_dotenv() is called.
    """
    global client
    global db
    
    # --- FIX: Retrieve the user's new env variable name ---
    MONGO_URI = os.getenv("MONGO_DB_URI")
    
    if not MONGO_URI:
        print("Configuration Error: MONGO_DB_URI environment variable not set.")
        return
    # --------------------------------------------------------

    if client is None:
        try:
            client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
            
            # Check connection status (optional, but good for debugging)
            client.admin.command('ping')
            
            # Use the explicitly defined project database name
            db = client[DB_NAME] 
            print("MongoDB connection established successfully.")
            
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            # In a real app, you might want to raise an exception or handle this more gracefully
            pass