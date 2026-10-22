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

    # Los errores de requests incluyen la URL completa, y la URL lleva la
    # clave. Por eso se sustituyen por mensajes propios sin la URL ("from
    # None" evita que el error original se imprima debajo).
    try:
        response = requests.get(
            f"{URL_BASE}/{endpoint}",
            params=params,
            timeout=30,
        )
    except requests.RequestException as error:
        raise RuntimeError(
            f"No se pudo conectar con FMP ({type(error).__name__}) "
            f"al pedir {endpoint} de {symbol}."
        ) from None

    if not response.ok:
        raise RuntimeError(
            f"FMP respondió {response.status_code} al pedir {endpoint} de {symbol}."
        )

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


def get_profile(symbol):
    # Perfil y cotización actual (precio, capitalización, sector...). Es una
    # sola fila: FMP ignora "period" y "limit" en este endpoint.
    return _get_estado_financiero("profile", symbol, limit=1)
