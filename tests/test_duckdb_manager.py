import pandas as pd
import pytest

from src.database.duckdb_manager import (
    guardar_estado,
    obtener_datos_analisis,
    obtener_estado,
)


@pytest.fixture
def ruta_db(tmp_path):
    # Base de datos temporal y vacía para cada test: nunca toca la real.
    return str(tmp_path / "test.duckdb")


def estado(symbol, años, valor=100):
    return pd.DataFrame(
        {
            "symbol": [symbol] * len(años),
            "date": pd.to_datetime([f"{año}-12-31" for año in años]),
            "total_assets": [valor] * len(años),
        }
    )


def test_guardar_y_leer(ruta_db):
    guardar_estado(estado("AAPL", [2024, 2025]), "balance_sheet", ruta_db)

    leido = obtener_estado("balance_sheet", ruta_db=ruta_db)

    assert len(leido) == 2
    assert leido["symbol"].tolist() == ["AAPL", "AAPL"]


def test_acumula_empresas_distintas(ruta_db):
    guardar_estado(estado("AAPL", [2025]), "balance_sheet", ruta_db)
    guardar_estado(estado("MSFT", [2025]), "balance_sheet", ruta_db)

    leido = obtener_estado("balance_sheet", ruta_db=ruta_db)

    assert leido["symbol"].tolist() == ["AAPL", "MSFT"]


def test_volver_a_guardar_sustituye_sin_duplicar(ruta_db):
    guardar_estado(estado("AAPL", [2024, 2025], valor=100), "balance_sheet", ruta_db)
    guardar_estado(estado("AAPL", [2025], valor=999), "balance_sheet", ruta_db)

    leido = obtener_estado("balance_sheet", ruta_db=ruta_db)

    assert len(leido) == 2
    assert leido["total_assets"].tolist() == [100, 999]


def test_filtrar_por_symbols(ruta_db):
    for symbol in ["AAPL", "MSFT", "KO"]:
        guardar_estado(estado(symbol, [2025]), "balance_sheet", ruta_db)

    leido = obtener_estado("balance_sheet", symbols=["KO", "AAPL"], ruta_db=ruta_db)

    assert leido["symbol"].tolist() == ["AAPL", "KO"]


def test_rechaza_tablas_no_permitidas(ruta_db):
    with pytest.raises(ValueError, match="Tabla no permitida"):
        guardar_estado(estado("AAPL", [2025]), "otra_tabla; DROP TABLE x", ruta_db)

    with pytest.raises(ValueError, match="Tabla no permitida"):
        obtener_estado("usuarios", ruta_db=ruta_db)


def guardar_tres_estados(ruta_db, symbol, años, inventario_flujos=-999):
    fechas = pd.to_datetime([f"{año}-12-31" for año in años])
    comun = {
        "symbol": [symbol] * len(años),
        "date": fechas,
        "fiscal_year": [str(año) for año in años],
        "reported_currency": ["USD"] * len(años),
        "fuente": ["FMP"] * len(años),
        "fecha_extraccion_utc": [pd.Timestamp("2026-10-16")] * len(años),
    }
    balance = pd.DataFrame(
        comun
        | {
            "total_assets": 400,
            "total_debt": 100,
            "total_stockholders_equity": 80,
            "total_current_assets": 150,
            "total_current_liabilities": 100,
            "inventory": 10,
            "cash_and_cash_equivalents": 40,
        }
    )
    resultados = pd.DataFrame(
        comun
        | {
            "revenue": 500,
            "gross_profit": 200,
            "operating_income": 150,
            "net_income": 120,
        }
    )
    flujos = pd.DataFrame(
        comun
        | {
            "net_income": 120,
            "inventory": inventario_flujos,
            "operating_cash_flow": 180,
            "capital_expenditure": -30,
        }
    )
    guardar_estado(balance, "balance_sheet", ruta_db)
    guardar_estado(resultados, "income_statement", ruta_db)
    guardar_estado(flujos, "cash_flow_statement", ruta_db)


def test_datos_analisis_une_los_tres_estados(ruta_db):
    guardar_tres_estados(ruta_db, "AAPL", [2024, 2025])

    df = obtener_datos_analisis(ruta_db=ruta_db)

    assert len(df) == 2
    fila = df.iloc[0]
    assert fila["total_assets"] == 400
    assert fila["revenue"] == 500
    assert fila["operating_cash_flow"] == 180


def test_datos_analisis_usa_el_inventario_del_balance(ruta_db):
    # En flujos, "inventory" es la variación del año: nunca debe colarse.
    guardar_tres_estados(ruta_db, "AAPL", [2025], inventario_flujos=-999)

    df = obtener_datos_analisis(ruta_db=ruta_db)

    assert df["inventory"].tolist() == [10]
    assert list(df.columns).count("inventory") == 1


def test_datos_analisis_descarta_años_que_no_estan_en_los_tres(ruta_db):
    guardar_tres_estados(ruta_db, "AAPL", [2024, 2025])
    # Un balance de 2023 sin cuenta de resultados ni flujos de ese año.
    guardar_estado(estado("AAPL", [2023]), "balance_sheet", ruta_db)

    df = obtener_datos_analisis(ruta_db=ruta_db)

    assert df["fiscal_year"].tolist() == ["2024", "2025"]


def test_datos_analisis_filtra_por_symbols(ruta_db):
    for symbol in ["AAPL", "MSFT", "KO"]:
        guardar_tres_estados(ruta_db, symbol, [2025])

    df = obtener_datos_analisis(symbols=["KO", "AAPL"], ruta_db=ruta_db)

    assert df["symbol"].tolist() == ["AAPL", "KO"]
