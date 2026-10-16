import pytest

from src import pipeline

# Respuestas falsas con la misma forma que las de FMP (camelCase, lista de
# diccionarios). Así el pipeline se prueba entero sin llamar a la API.
BALANCE_FMP = [
    {
        "date": "2025-09-27",
        "symbol": "AAPL",
        "reportedCurrency": "USD",
        "fiscalYear": "2025",
        "totalAssets": 400,
        "totalDebt": 100,
        "cashAndCashEquivalents": 40,
        "netDebt": 60,
        "totalStockholdersEquity": 80,
        "totalCurrentAssets": 150,
        "inventory": 10,
        "totalCurrentLiabilities": 100,
    }
]

RESULTADOS_FMP = [
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

FLUJOS_FMP = [
    {
        "date": "2025-09-27",
        "symbol": "AAPL",
        "reportedCurrency": "USD",
        "fiscalYear": "2025",
        "netIncome": 120,
        # En flujos, "inventory" es la variación del año, no el saldo: tiene
        # un valor absurdo a propósito para detectar si se colara en los ratios.
        "inventory": -999,
        "operatingCashFlow": 180,
        "capitalExpenditure": -30,
        "freeCashFlow": 150,
    }
]


@pytest.fixture
def api_falsa(monkeypatch):
    # monkeypatch sustituye, solo durante el test, las funciones que llaman
    # a FMP por otras que devuelven los datos de arriba.
    monkeypatch.setattr(pipeline, "get_balance_sheet", lambda s, limit: BALANCE_FMP)
    monkeypatch.setattr(
        pipeline, "get_income_statement", lambda s, limit: RESULTADOS_FMP
    )
    monkeypatch.setattr(
        pipeline, "get_cash_flow_statement", lambda s, limit: FLUJOS_FMP
    )


def test_pipeline_completo_sin_api(api_falsa, tmp_path):
    ruta_db = str(tmp_path / "test.duckdb")

    pipeline.actualizar_empresa("AAPL", num_periodos=1, ruta_db=ruta_db)
    ratios = pipeline.obtener_ratios(["AAPL"], ruta_db=ruta_db)

    fila = ratios.iloc[0]
    assert fila["symbol"] == "AAPL"
    assert fila["fuente"] == "Financial Modeling Prep"
    assert fila["deuda_sobre_activos"] == pytest.approx(0.25)
    assert fila["liquidez_corriente"] == pytest.approx(1.5)
    assert fila["margen_neto"] == pytest.approx(0.24)
    assert fila["roa"] == pytest.approx(0.30)
    assert fila["roe"] == pytest.approx(1.50)
    assert fila["flujo_caja_libre"] == 150
    assert fila["margen_fcf"] == pytest.approx(0.30)
    assert fila["calidad_beneficio"] == pytest.approx(1.50)
    # La prueba ácida usa el inventario del balance (10), no el de flujos.
    assert fila["prueba_acida"] == pytest.approx(1.40)


def test_si_no_valida_no_guarda_nada(api_falsa, tmp_path):
    ruta_db = str(tmp_path / "test.duckdb")

    # Pedimos 5 periodos pero la "API" solo devuelve 1: la validación falla.
    with pytest.raises(ValueError, match="Se esperaban 5"):
        pipeline.actualizar_empresa("AAPL", num_periodos=5, ruta_db=ruta_db)

    assert not (tmp_path / "test.duckdb").exists()
