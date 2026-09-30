import os

import requests
from dotenv import load_dotenv


load_dotenv()


def get_balance_sheet(symbol, limit=5):

    api_key = os.getenv("API_KEY")

    if not api_key:
        raise RuntimeError("No se encontró API_KEY en el archivo .env.")

    url = "https://financialmodelingprep.com/stable/balance-sheet-statement"

    params = {
        "symbol": symbol,
        "period": "annual",
        "limit": limit,
        "apikey": api_key,
    }

    response = requests.get(
        url,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()