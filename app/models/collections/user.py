from app.database.db import db
from datetime import datetime, timezone
from bson.objectid import ObjectId


class User:
    """
    Model class to handle database operations for the 'users' collection.
    """

    @staticmethod
    def get_collection():
        """Helper to get the MongoDB collection or None if DB is not ready."""
        if db is None:
            return None
        return db['users']

    @staticmethod
    def create_user(line_account_id: str = None, google_account_id: str = None, yahoo_account_id: str = None):
        """Creates a user document WITHOUT a username initially."""
        collection = User.get_collection()
        if collection is None:
            return None

        user_data = {
            "username": None,  # Explicitly null until onboarding
            "totalContributions": 0,
            "rankScore": 0,
            "hostRating": {"totalPoints": 0, "totalRatings": 0},
            "totalExpenditure": 0.0,
            "estimatedTotalSavings": 0.0,
            "joinedAt": datetime.now(timezone.utc)
        }

        if line_account_id:
            user_data["lineAccountId"] = line_account_id
        if google_account_id:
            user_data["googleAccountId"] = google_account_id
        if yahoo_account_id:
            user_data["yahooAccountId"] = yahoo_account_id

        try:
            # Partial index for username so we can have multiple 'null' usernames initially
            collection.create_index([("username", 1)], unique=True, partialFilterExpression={
                                    "username": {"$type": "string"}})

            # Social ID indices (Unique only if field exists)
            if "lineAccountId" in user_data:
                collection.create_index([("lineAccountId", 1)], unique=True, partialFilterExpression={
                                        "lineAccountId": {"$exists": True}})
            if "googleAccountId" in user_data:
                collection.create_index([("googleAccountId", 1)], unique=True, partialFilterExpression={
                                        "googleAccountId": {"$exists": True}})
            if "yahooAccountId" in user_data:
                collection.create_index([("yahooAccountId", 1)], unique=True, partialFilterExpression={
                                        "yahooAccountId": {"$exists": True}})

            result = collection.insert_one(user_data)
            return result.inserted_id
        except Exception as e:
            print(f"Error creating user: {e}")
            return None

    @staticmethod
    def assign_username(user_id: str, chosen_username: str):
        """Sets the username ONLY if it is currently null/None."""
        collection = User.get_collection()
        if collection is None or not ObjectId.is_valid(user_id):
            return False

        # Atomically update only if username is still None
        result = collection.update_one(
            {"_id": ObjectId(user_id), "username": None},
            {"$set": {"username": chosen_username}}
        )
        return result.modified_count == 1

    @staticmethod
    def get_user_by_social_id(social_id: str, provider: str):
        """Retrieves full user document by social provider ID."""
        collection = User.get_collection()
        if collection is None:
            return None
        field_map = {'google': 'googleAccountId',
                     'line': 'lineAccountId', 'yahoo': 'yahooAccountId'}
        field = field_map.get(provider)
        return collection.find_one({field: social_id})

    @staticmethod
    def get_by_id(user_id: str):
        """Retrieves user by MongoDB ObjectId string."""
        collection = User.get_collection()
        if collection is None or not ObjectId.is_valid(user_id):
            return None
        return collection.find_one({"_id": ObjectId(user_id)})

    @staticmethod
    def update_estimated_savings(user_id: str, savings_amount: float):
        collection = User.get_collection()
        if collection is None or not ObjectId.is_valid(user_id):
            return False
        result = collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$inc": {"estimatedTotalSavings": savings_amount}}
        )
        return result.modified_count == 1
