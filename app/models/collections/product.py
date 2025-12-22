from app import db
from datetime import datetime, timezone
from difflib import SequenceMatcher

class Product:
    # Simple in-memory cache to avoid fetching all products every time
    # Structure: [{'id': ObjectId, 'name': 'Coca Cola', 'aliases': []}, ...]
    _product_cache = None
    _last_cache_update = None

    @staticmethod
    def get_collection():
        if db is None:
            return None
        return db['products']

    @staticmethod
    def _refresh_cache(collection):
        """
        Refreshes the internal product name cache. 
        In production, you might use Redis or a proper caching strategy.
        """
        cursor = collection.find({}, {"name": 1, "aliases": 1})
        Product._product_cache = list(cursor)
        Product._last_cache_update = datetime.now()

    @staticmethod
    def _find_best_match(collection, input_name, threshold=0.85):
        """
        Finds the best matching product using a tiered approach:
        1. Exact Match (Name or Alias)
        2. Fuzzy Match (Similarity > threshold)
        """
        # 1. Exact DB Lookup (Fastest)
        # Check if input_name matches 'name' OR exists in 'aliases' array
        exact_match = collection.find_one({
            "$or": [
                {"name": input_name},
                {"aliases": input_name}
            ]
        })
        if exact_match:
            return exact_match, 1.0  # 1.0 = 100% match

        # 2. Fuzzy Matching (Slower - requires cache)
        # If cache is empty or old (e.g., > 5 mins), refresh it
        if Product._product_cache is None:
             Product._refresh_cache(collection)

        best_doc = None
        best_ratio = 0.0

        for doc in Product._product_cache:
            # Compare with canonical name
            ratio = SequenceMatcher(None, input_name, doc.get('name', '')).ratio()
            
            # If canonical didn't match well, check aliases
            if ratio < threshold and 'aliases' in doc:
                for alias in doc['aliases']:
                    alias_ratio = SequenceMatcher(None, input_name, alias).ratio()
                    if alias_ratio > ratio:
                        ratio = alias_ratio
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_doc = doc

        if best_ratio >= threshold:
            return best_doc, best_ratio
        
        return None, 0.0

    @staticmethod
    def bulk_upsert(store_name: str, products_data: list):
        """
        Updates product prices with Fuzzy Matching and Aliasing.
        """
        collection = Product.get_collection()
        if collection is None:
            return 0
        
        # --- Index Creation ---
        try:
            collection.create_index([("name", 1)])
            collection.create_index([("aliases", 1)])
            collection.create_index([("prices", 1)])
        except Exception as e:
            print(f"Error creating product indexes: {e}")
        
        updated_count = 0
        now = datetime.now(timezone.utc)
        
        for item in products_data:
            input_name = item.get('name')
            english_name = item.get('english_name')
            price = item.get('price')
            
            if not input_name or price is None:
                continue

            try:
                # --- STEP 1: Find Canonical Product ---
                existing_product, similarity = Product._find_best_match(collection, input_name)
                
                should_update = False
                is_fuzzy_match = False

                if not existing_product:
                    # Case: Brand New Product
                    collection.insert_one({
                        "name": input_name,
                        "englishName": english_name,
                        "aliases": [], # Initialize empty alias list
                        "prices": {
                            store_name: {
                                "price": price,
                                "date": now
                            }
                        }
                    })
                    # Add to cache to make it available for next items in this loop
                    if Product._product_cache is not None:
                        Product._product_cache.append({"name": input_name, "aliases": []})
                    
                    updated_count += 1
                    continue

                # Case: Found Existing Product (Exact or Fuzzy)
                # If similarity is < 1.0, it means we found it via fuzzy match.
                # We should add the 'input_name' to the 'aliases' of the existing product
                # so future lookups are exact.
                if similarity < 1.0:
                    is_fuzzy_match = True

                prices = existing_product.get('prices', {})
                existing_store_data = prices.get(store_name)
                
                # --- STEP 2: Price Update Logic ---
                if existing_store_data is None:
                    should_update = True
                else:
                    last_date = existing_store_data.get('date')
                    if last_date and isinstance(last_date, datetime):
                        if last_date < now:
                             should_update = True
                    else:
                        should_update = True
                
                # --- STEP 3: Perform Update ---
                # Prepare update query
                update_query = {}
                set_fields = {}
                add_to_set_fields = {}

                if should_update:
                    set_fields[f"prices.{store_name}"] = {"price": price, "date": now}
                    # Always update English name to latest (or keep existing if current is better?)
                    # Let's overwrite for now to keep it simple
                    set_fields["englishName"] = english_name
                
                if is_fuzzy_match:
                    # Add the new variation to aliases so next time it's an exact match
                    add_to_set_fields["aliases"] = input_name

                # Construct MongoDB Query
                if set_fields:
                    update_query["$set"] = set_fields
                
                if add_to_set_fields:
                    update_query["$addToSet"] = add_to_set_fields

                if update_query:
                    collection.update_one(
                        {"_id": existing_product["_id"]},
                        update_query
                    )
                    updated_count += 1

            except Exception as e:
                print(f"Error upserting product {input_name}: {e}")
                
        # Invalidate cache after batch operation so next request fetches fresh data
        Product._product_cache = None
        
        return updated_count