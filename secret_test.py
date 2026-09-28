import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")

print("¿Tenemos API Key?", api_key is not None)