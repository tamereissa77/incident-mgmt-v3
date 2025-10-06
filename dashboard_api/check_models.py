import os
import google.generativeai as genai

# --- Configuration ---
# This will load the same API key your main application uses
try:
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if not GOOGLE_API_KEY:
        print("ERROR: GOOGLE_API_KEY environment variable is not set.")
        exit(1)
        
    genai.configure(api_key=GOOGLE_API_KEY)
    print("Google AI client configured successfully.")

except Exception as e:
    print(f"An error occurred during configuration: {e}")
    exit(1)

# --- List Available Models ---
print("\n--- Querying for available models... ---")
try:
    for model in genai.list_models():
        # We only care about models that support the 'generateContent' method
        if 'generateContent' in model.supported_generation_methods:
            print(f"Model Name: {model.name}")

except Exception as e:
    print(f"\nAn error occurred while listing models: {e}")
    print("This likely confirms that your API key is valid but may not have the right permissions,")
    print("or the client library is too old to find compatible models on the endpoint it's using.")

print("\n--- Query complete. ---")