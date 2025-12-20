import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Test simple API call
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content("Say hello")

print("Response:")
print(response.text)
print("\nResponse type:", type(response))
print("Has text:", hasattr(response, 'text'))
