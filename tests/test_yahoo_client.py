import math

import pytest

from src.data import yahoo_client


class TickerFalso:
    # Imita a yfinance.Ticker: solo hace falta su atributo "info".
    def __init__(self, info):
        self.info = info


def test_perfil_traducido_a_los_nombres_del_motor(monkeypatch):
    info = {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "currentPrice": 338.32,
        "regularMarketChangePercent": -1.83,
        "marketCap": 4_937_503_211_520,
        "currency": "USD",
    }
    monkeypatch.setattr(yahoo_client.yf, "Ticker", lambda s: TickerFalso(info))

    perfil = yahoo_client.get_profile("AAPL")[0]

    assert perfil["symbol"] == "AAPL"
    assert perfil["companyName"] == "Apple Inc."
    assert perfil["price"] == 338.32
    assert perfil["changePercentage"] == -1.83
    assert perfil["marketCap"] == 4_937_503_211_520


def test_dato_que_yahoo_no_da_queda_vacio(monkeypatch):
    monkeypatch.setattr(yahoo_client.yf, "Ticker", lambda s: TickerFalso({}))

    perfil = yahoo_client.get_profile("XYZ")[0]

    assert math.isnan(perfil["marketCap"])
    assert perfil["sector"] is None


def test_fallo_de_yahoo_da_un_error_propio(monkeypatch):
    class TickerQueFalla:
        @property
        def info(self):
            raise ConnectionError("Yahoo caído")

    monkeypatch.setattr(yahoo_client.yf, "Ticker", lambda s: TickerQueFalla())

    with pytest.raises(RuntimeError, match="perfil de XYZ en Yahoo"):
        yahoo_client.get_profile("XYZ")
