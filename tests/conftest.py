# Fixtures compartidas por varios archivos de tests (pytest las encuentra
# solo, sin importarlas).
import pytest

from src import pipeline

# Respuestas falsas con la misma forma que devuelven sec_client y yahoo_client
# (camelCase, lista de diccionarios). Así el pipeline se prueba entero sin
# llamar a internet.
BALANCE_FALSO = [
    {
        "date": "2025-09-27",
        "symbol": "AAPL",
        "reportedCurrency": "USD",
        "fiscalYear": "2025",
        "totalAssets": 400,
        "totalDebt": 100,
        "cashAndCashEquivalents": 40,
        "totalLiabilitiesAndTotalEquity": 400,
        "totalStockholdersEquity": 80,
        "totalCurrentAssets": 150,
        "inventory": 10,
        "totalCurrentLiabilities": 100,
    }
]

RESULTADOS_FALSOS = [
    {
        "date": "2025-09-27",
        "symbol": "AAPL",
        "reportedCurrency": "USD",
        "fiscalYear": "2025",
        "revenue": 500,
        "grossProfit": 200,
        "operatingIncome": 150,
        "netIncome": 120,
    }
]

FLUJOS_FALSOS = [
    {
        "date": "2025-09-27",
        "symbol": "AAPL",
        "reportedCurrency": "USD",
        "fiscalYear": "2025",
        # En flujos, "inventory" es la variación del año, no el saldo: tiene
        # un valor absurdo a propósito para detectar si se colara en los ratios.
        "inventory": -999,
        "operatingCashFlow": 180,
        "capitalExpenditure": -30,
    }
]

# Sin "date", como el perfil real. PER esperado = 2400 / 120 = 20.
PERFIL_FALSO = [
    {
        "symbol": "AAPL",
        "companyName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "price": 150.5,
        "changePercentage": -0.15,
        "marketCap": 2400,
        "currency": "USD",
    }
]


@pytest.fixture
def api_falsa(monkeypatch):
    # monkeypatch sustituye, solo durante el test, las funciones que llaman
    # a internet por otras que devuelven los datos de arriba.
    monkeypatch.setattr(pipeline, "get_balance_sheet", lambda s, limit: BALANCE_FALSO)
    monkeypatch.setattr(
        pipeline, "get_income_statement", lambda s, limit: RESULTADOS_FALSOS
    )
    monkeypatch.setattr(
        pipeline, "get_cash_flow_statement", lambda s, limit: FLUJOS_FALSOS
    )
    monkeypatch.setattr(pipeline, "get_profile", lambda s: PERFIL_FALSO)
