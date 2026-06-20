import os
import sys
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv(override=True)

api_key = os.environ.get('GEMINI_API_KEY')
print(f"Loaded API Key: {api_key[:5]}...{api_key[-5:]}" if api_key else "No API Key found")

try:
    genai.configure(api_key=api_key)
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Exception caught: {type(e).__name__} - {str(e)}")
