import os

import requests
from dotenv import load_dotenv

load_dotenv()

URL_BASE = "https://financialmodelingprep.com/stable"


def _get_estado_financiero(endpoint, symbol, limit):
    api_key = os.getenv("API_KEY")

    if not api_key:
        raise RuntimeError("No se encontró API_KEY en el archivo .env.")

    params = {
        "symbol": symbol,
        "period": "annual",
        "limit": limit,
        "apikey": api_key,
    }

    response = requests.get(
        f"{URL_BASE}/{endpoint}",
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    datos = response.json()

    if not datos:
        raise ValueError(f"FMP no devolvió datos de {endpoint} para {symbol}.")

    return datos


def get_balance_sheet(symbol, limit=5):
    return _get_estado_financiero("balance-sheet-statement", symbol, limit)


def get_income_statement(symbol, limit=5):
    return _get_estado_financiero("income-statement", symbol, limit)


def get_cash_flow_statement(symbol, limit=5):
    return _get_estado_financiero("cash-flow-statement", symbol, limit)
