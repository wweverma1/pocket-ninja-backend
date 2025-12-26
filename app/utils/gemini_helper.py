import os
import json
import base64
import textwrap
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# --- Pydantic Models for Structured Output ---


class Product(BaseModel):
    name: str = Field(description="Original product name")
    english_name: str = Field(description="English translation of the product name")
    price: float = Field(description="Price of the product excluding discounts")


class ReceiptAnalysis(BaseModel):
    error_code: int = Field(
        description="0 for success. 3-7 for extraction errors. 1 for invalid image type. 2 for tampering detected.")
    store_name: Optional[str] = Field(description="The matched/extracted store name. Null if error_code is not 0.")
    total_amount: Optional[float] = Field(description="The total amount paid. 0.0 if error_code is not 0.")
    products: List[Product] = Field(description="List of extracted products. Empty if error_code is not 0.")


def get_receipt_analysis_instruction(date_str, target_city, available_stores):
    stores_list_str = ", ".join(available_stores)

    receipt_analysis_instruction = textwrap.dedent(f"""
        Instructions:
        You are an expert receipt analysis AI. Analyze the provided image and extract data 
        into the specified JSON format. Follow these validation steps in order:

        1. Image Validation (Safeguards):
           - Is the image a photograph of a physical receipt?
           - Is the receipt from a Convenience Store, Supermarket, or Drug Store?
           - Does the image appear authentic (NOT digitally edited, photoshopped, or screen-generated)?
           - If the image is NOT a receipt or NOT from a valid store type -> Set error_code to 1.
           - If the image appears edited or tampered with -> Set error_code to 2.
           - If valid, proceed to the next step.

        2. Analyze Billing Date:
           - Reference Date: {date_str}
           - Check if the receipt date is within 3 days (inclusive) BEFORE this reference date.
           - If date is too old or in the future -> Set error_code to 3.
           - If date is missing/unreadable -> Set error_code to 4.

        3. Analyze Store Location:
           - Check if the store address/branch is in {target_city}.
           - If NOT in {target_city} -> Set error_code to 5.
           - If location is missing/unreadable -> Set error_code to 6.

        4. Identify Store Name:
           - Match against this list: [{stores_list_str}].
           - If match found -> Use the standard list name.
           - If NO match -> Extract the generic brand name (exclude branch name).
           - If store name is missing/unreadable -> Set error_code to 7.

        5. Extract Data (Only if error_code is 0):
           - Extract "products": List of items (name, english_name, price).
           - Extract "total_amount": The Grand Total if possible.
           - Set error_code to 0.

        Constraint: If error_code is NOT 0, set 'store_name' to null, 'total_amount' to 0.0, and 'products' to [].
    """)
    return receipt_analysis_instruction


def analyze_receipt_with_gemini(image_bytes: bytes, instruction: str):
    """
    Sends the image and instruction to Gemini via the Google Gen AI SDK.
    Enforces structured output using Pydantic.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set.")
        return None

    try:
        # Initialize Client
        client = genai.Client(api_key=api_key)

        # Call Gemini 2.5 Flash
        # 2.5 Flash is currently the fastest model for this task.
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type='image/webp',
                ),
                instruction
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": ReceiptAnalysis,
            }
        )

        return json.loads(response.text)

    except Exception as e:
        print(f"Gemini Analysis Error: {e}")
        return None
