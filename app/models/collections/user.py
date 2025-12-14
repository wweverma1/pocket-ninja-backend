from app.database.db import db 
from datetime import datetime, timezone
from bson.objectid import ObjectId

class User:
    """
    Model class to handle database operations for the 'users' collection.
    
    Collection Key Properties:
    _id (ObjectId), username (unique), googleAccountId, lineAccountId, yahooAccountId, 
    totalContributions, rankScore, hostRating (totalPoints, totalRatings), 
    totalExpenditure, estimatedTotalSavings, joinedAt.
    """
    
    @staticmethod
    def get_collection():
        """Helper to get the MongoDB collection or None if DB is not ready."""
        if db is None:
            return None
        return db['users']

    @staticmethod
    def create_user(username: str, line_account_id: str = None, google_account_id: str = None, yahoo_account_id: str = None):
        """
        Creates a new user document.
        """
        collection = User.get_collection()

        if collection is None: 
            return None
        
        user_data = {
            "lineAccountId": line_account_id,
            "googleAccountId": google_account_id,
            "yahooAccountId": yahoo_account_id,
            "username": username,
            "totalContributions": 0,
            "rankScore": 0,
            "hostRating": {"totalPoints": 0, "totalRatings": 0},
            "totalExpenditure": 0.0,
            "estimatedTotalSavings": 0.0,
            "joinedAt": datetime.now(timezone.utc)
        }
        
        try:
            # Enforce uniqueness on username
            collection.create_index([("username", 1)], unique=True)

            # Enforce uniqueness on external social IDs (only if present)
            if line_account_id:
                collection.create_index([("lineAccountId", 1)], unique=True, partialFilterExpression={"lineAccountId": {"$exists": True, "$ne": None}})
            if google_account_id:
                collection.create_index([("googleAccountId", 1)], unique=True, partialFilterExpression={"googleAccountId": {"$exists": True, "$ne": None}})
            if yahoo_account_id:
                collection.create_index([("yahooAccountId", 1)], unique=True, partialFilterExpression={"yahooAccountId": {"$exists": True, "$ne": None}})
                
            result = collection.insert_one(user_data)
            return result.inserted_id
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    @staticmethod
    def get_id_by_social_account_id(social_id: str, provider: str):
        """
        Retrieves a user's MongoDB ObjectId (_id) by their social media ID and provider.
        """
        collection = User.get_collection()

        if collection is None:
            return None
            
        field_map = {
            'google': 'googleAccountId',
            'line': 'lineAccountId',
            'yahoo': 'yahooAccountId'
        }
        
        field = field_map.get(provider)
        if not field:
            return None

        # Project only the _id field for efficiency
        user = collection.find_one({field: social_id}, {"_id": 1})
        return user['_id'] if user else None

    @staticmethod
    def get_by_id(user_id: str):
        """
        Retrieves a user document by its MongoDB ObjectId.
        """
        collection = User.get_collection()

        if collection is None or not ObjectId.is_valid(user_id):
            return None
        
        return collection.find_one({"_id": ObjectId(user_id)})

    @staticmethod
    def update_estimated_savings(user_id: str, savings_amount: float):
        """
        Updates the user's estimatedTotalSavings using the MongoDB ObjectId.
        """
        collection = User.get_collection()

        if collection is None or not ObjectId.is_valid(user_id):
            return False
        
        result = collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"estimatedTotalSavings": savings_amount}} 
        )
        return result.modified_count == 1