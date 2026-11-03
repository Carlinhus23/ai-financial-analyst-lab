# Perfil y cotización actual desde Yahoo Finance (librería yfinance), gratis y
# sin clave. La SEC no da precios: Yahoo pone el precio, la capitalización y
# el sector. Devuelve los mismos nombres que usaba FMP.

import yfinance as yf

VACIO = float("nan")


def get_profile(symbol):
    # yfinance no es un servicio oficial: si Yahoo falla o cambia, se avisa
    # con un mensaje propio.
    try:
        info = yf.Ticker(symbol).info
    except Exception as error:
        raise RuntimeError(
            f"No se pudo obtener el perfil de {symbol} en Yahoo "
            f"({type(error).__name__})."
        ) from None

    # "or VACIO": si Yahoo no da el dato (None), queda vacío (NaN).
    return [
        {
            "symbol": symbol,
            "companyName": info.get("longName"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "price": info.get("currentPrice") or VACIO,
            "changePercentage": info.get("regularMarketChangePercent") or VACIO,
            "marketCap": info.get("marketCap") or VACIO,
            "currency": info.get("currency"),
        }
    ]
