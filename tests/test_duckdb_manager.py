import pandas as pd
import pytest

from src.database.duckdb_manager import guardar_estado, obtener_estado


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
