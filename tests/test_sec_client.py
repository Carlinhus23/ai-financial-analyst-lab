import math

import pytest

from src.data import sec_client

CIK_FALSO = "0000000001"


def hecho(valor, fin, inicio=None, form="10-K", presentado="2026-01-30"):
    # Una cifra XBRL como las de la SEC. Sin "inicio" es un saldo (balance);
    # con "inicio" es un importe de un periodo (ventas, flujos).
    fila = {"val": valor, "end": fin, "form": form, "filed": presentado}
    if inicio:
        fila["start"] = inicio
    return fila


def etiqueta(*hechos):
    return {"units": {"USD": list(hechos)}}


def año(fin, inicio, activo=400, deuda_corriente=None):
    # Las cifras de un año: un balance que cuadra y una cuenta de resultados.
    cifras = {
        "Assets": [hecho(activo, fin)],
        "LiabilitiesAndStockholdersEquity": [hecho(activo, fin)],
        "LongTermDebtNoncurrent": [hecho(80, fin)],
        "LongTermDebtCurrent": [hecho(10, fin)],
        "CommercialPaper": [hecho(5, fin)],
        "Revenues": [hecho(500, fin, inicio)],
        "CostOfRevenue": [hecho(300, fin, inicio)],
        "NetIncomeLoss": [hecho(120, fin, inicio)],
        "NetCashProvidedByUsedInOperatingActivities": [hecho(180, fin, inicio)],
        "PaymentsToAcquireProductiveAssets": [hecho(30, fin, inicio)],
    }
    if deuda_corriente is not None:
        cifras["DebtCurrent"] = [hecho(deuda_corriente, fin)]
    return cifras


def unir(*años):
    hechos = {}
    for cifras in años:
        for nombre, filas in cifras.items():
            hechos.setdefault(nombre, etiqueta())["units"]["USD"].extend(filas)
    return hechos


@pytest.fixture
def sec_falsa(monkeypatch):
    # Sustituye las descargas por datos inventados y vacía la memoria de
    # functools.cache antes y después, para que un test no contamine a otro.
    datos = {"hechos": {}}

    def get_json_falso(url):
        if url == sec_client.URL_TICKERS:
            return {"0": {"ticker": "XYZ", "cik_str": 1}}
        assert CIK_FALSO in url
        return {"facts": {"us-gaap": datos["hechos"]}}

    monkeypatch.setattr(sec_client, "_get_json", get_json_falso)
    sec_client._ciks.cache_clear()
    sec_client._hechos.cache_clear()
    yield datos
    sec_client._ciks.cache_clear()
    sec_client._hechos.cache_clear()


def test_balance_ultimos_años_y_deuda_sumando_piezas(sec_falsa):
    sec_falsa["hechos"] = unir(
        año("2025-12-31", "2025-01-01"),
        año("2024-12-31", "2024-01-01", activo=300),
        año("2023-12-31", "2023-01-01", activo=200),
    )

    balances = sec_client.get_balance_sheet("XYZ", limit=2)

    assert [b["fiscalYear"] for b in balances] == ["2025", "2024"]
    assert balances[0]["totalAssets"] == 400
    # Siempre decimales: con enteros, DuckDB devolvería los huecos como <NA>
    assert isinstance(balances[0]["totalAssets"], float)
    # Sin DebtCurrent: 80 (no corriente) + 10 (largo que vence) + 5 (pagarés)
    assert balances[0]["totalDebt"] == 95
    # Sin existencias en la fuente: vacío, no cero
    assert math.isnan(balances[0]["inventory"])


def test_si_hay_deuda_corriente_total_no_suma_las_piezas(sec_falsa):
    sec_falsa["hechos"] = unir(año("2025-12-31", "2025-01-01", deuda_corriente=12))

    balance = sec_client.get_balance_sheet("XYZ")[0]

    assert balance["totalDebt"] == 80 + 12


def test_resultados_y_flujos_traducidos(sec_falsa):
    sec_falsa["hechos"] = unir(año("2025-12-31", "2025-01-01"))

    resultados = sec_client.get_income_statement("XYZ")[0]
    flujos = sec_client.get_cash_flow_statement("XYZ")[0]

    assert resultados["revenue"] == 500
    # Sin GrossProfit en la fuente: ventas - coste de ventas
    assert resultados["grossProfit"] == 200
    assert math.isnan(resultados["operatingIncome"])
    # El pago de capex (30) pasa a negativo
    assert flujos["capitalExpenditure"] == -30


def test_ignora_trimestres_y_10q_y_usa_la_ultima_cuenta_presentada(sec_falsa):
    hechos = unir(año("2025-12-31", "2025-01-01"))
    hechos["Revenues"]["units"]["USD"] = [
        hecho(140, "2025-12-31", "2025-10-01"),  # un trimestre: no vale
        hecho(999, "2025-12-31", "2025-01-01", form="10-Q"),  # no es anual
        hecho(500, "2025-12-31", "2025-01-01", presentado="2026-01-30"),
        hecho(510, "2025-12-31", "2025-01-01", presentado="2027-01-29"),  # revisada
    ]
    sec_falsa["hechos"] = hechos

    assert sec_client.get_income_statement("XYZ")[0]["revenue"] == 510


def test_ejercicio_que_cierra_a_primeros_de_enero_es_del_año_anterior():
    assert sec_client._ejercicio("2023-01-01") == "2022"
    assert sec_client._ejercicio("2026-01-31") == "2026"
    assert sec_client._ejercicio("2025-09-27") == "2025"


def test_empresa_que_no_esta_en_la_sec(sec_falsa):
    with pytest.raises(ValueError, match="no tiene la empresa NOEXISTE"):
        sec_client.get_balance_sheet("NOEXISTE")


def test_cik_manual_tiene_prioridad_sobre_la_tabla_de_la_sec(sec_falsa, monkeypatch):
    # La tabla falsa no tiene "ABC", pero la excepción manual sí.
    monkeypatch.setitem(sec_client.CIKS_MANUALES, "ABC", CIK_FALSO)
    sec_falsa["hechos"] = unir(año("2025-12-31", "2025-01-01"))

    assert sec_client.get_balance_sheet("ABC")[0]["totalAssets"] == 400


def test_sin_user_agent_avisa(monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)

    with pytest.raises(RuntimeError, match="SEC_USER_AGENT"):
        sec_client._get_json(sec_client.URL_TICKERS)


def test_url_10k_usa_el_ticker():
    url = sec_client.url_10k("AAPL")

    assert "CIK=AAPL" in url
    assert "type=10-K" in url


def test_url_10k_de_exxon_usa_su_cik_manual():
    # El ticker XOM ya apunta a la holding nueva, que aún no tiene 10-K.
    assert "CIK=0000034088" in sec_client.url_10k("XOM")
