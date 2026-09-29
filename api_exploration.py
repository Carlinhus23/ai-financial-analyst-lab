import os

import requests
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("API_KEY")

url = "https://financialmodelingprep.com/stable/balance-sheet-statement"

params = {
    "symbol": "AAPL",
    "period": "annual",
    "limit": 5,
    "apikey": api_key,
}

response = requests.get(url, params=params, timeout=30)

print(response.status_code)

datos = response.json()
for balance in datos:
    print(balance["date"], balance["totalAssets"])

print(type(datos))
print(len(datos))
print(datos[0])