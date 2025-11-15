# utils/api_key_manager.py
import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Load environment variables from .env file (for local testing)
load_dotenv()

class ApiKeyManager:
    """Manages a list of Gemini API keys and rotates them on quota failure."""
    def __init__(self):
        keys_str = os.getenv("GEMINI_API_KEYS")
        if not keys_str:
            # This will be the main error if the environment variable isn't set on Render
            print("CRITICAL ERROR: GEMINI_API_KEYS environment variable not set.")
            self.keys = []
        else:
            self.keys = [key.strip() for key in keys_str.split(',')]
        
        self.current_key_index = 0
        self.total_keys = len(self.keys)

    def get_next_key(self):
        """Rotates to the next key in the list."""
        self.current_key_index = (self.current_key_index + 1) % self.total_keys
        return self.keys[self.current_key_index]

# Create a single instance of the manager to be used by the app
key_manager = ApiKeyManager()

async def make_gemini_request(prompt: str):
    """
    Makes a request to the Gemini API, automatically handling key rotation
    on ResourceExhausted (429) errors.
    """
    if not key_manager.keys:
        return "Error: No API keys are configured."

    # Try each key once in a full cycle
    for _ in range(key_manager.total_keys):
        try:
            # Configure the library with the current key
            current_key = key_manager.keys[key_manager.current_key_index]
            genai.configure(api_key=current_key)
            model = genai.GenerativeModel('gemini-2.5-flash')

            # Make the API call
            response = await model.generate_content_async(prompt)
            # If successful, return the text and exit the loop
            return response.text

        except google_exceptions.ResourceExhausted as e:
            # This error means the daily quota was hit (HTTP 429)
            print(f"Key index {key_manager.current_key_index} quota exceeded. Rotating to next key.")
            key_manager.get_next_key()  # Rotate to the next key for the next request
            
            # Continue the loop to try the next key immediately
            continue
        
        except Exception as e:
            # Handle other potential errors (invalid key, network issues, etc.)
            print(f"An unexpected error occurred with key index {key_manager.current_key_index}: {e}")
            key_manager.get_next_key() # Also rotate on other errors
            continue

    return "All available API keys have failed or exceeded their quota."