import pandas as pd
import pytest

from src.data.transformer import (
    añadir_trazabilidad,
    convertir_a_snake_case,
    estado_a_dataframe,
    unir_estados,
)


def test_convertir_a_snake_case():
    assert convertir_a_snake_case("totalAssets") == "total_assets"
    assert convertir_a_snake_case("symbol") == "symbol"


def test_estado_a_dataframe_convierte_columnas_y_fechas():
    datos = [{"date": "2025-09-27", "symbol": "AAPL", "totalAssets": 100}]

    df = estado_a_dataframe(datos)

    assert list(df.columns) == ["date", "symbol", "total_assets"]
    assert df["date"].iloc[0] == pd.Timestamp("2025-09-27")


def test_anadir_trazabilidad_con_fecha_dada():
    df = pd.DataFrame({"symbol": ["AAPL", "AAPL"]})
    fecha = pd.Timestamp("2026-10-11 09:30")

    resultado = añadir_trazabilidad(df, fuente="FMP", fecha_extraccion=fecha)

    assert (resultado["fuente"] == "FMP").all()
    assert (resultado["fecha_extraccion_utc"] == fecha).all()
    assert "fuente" not in df.columns


def test_anadir_trazabilidad_sin_fecha_usa_ahora():
    antes = pd.Timestamp.now(tz="UTC").tz_localize(None)

    resultado = añadir_trazabilidad(pd.DataFrame({"symbol": ["AAPL"]}), "FMP")

    despues = pd.Timestamp.now(tz="UTC").tz_localize(None)
    assert antes <= resultado["fecha_extraccion_utc"].iloc[0] <= despues


def test_unir_estados_empareja_por_empresa_y_fecha():
    fecha = pd.Timestamp("2025-12-31")
    balance = pd.DataFrame(
        {
            "symbol": ["AAPL", "MSFT"],
            "date": [fecha, fecha],
            "total_assets": [100, 200],
            "reported_currency": ["USD", "USD"],
        }
    )
    resultados = pd.DataFrame(
        {
            "symbol": ["MSFT", "AAPL"],  # orden distinto a propósito
            "date": [fecha, fecha],
            "net_income": [20, 10],
            "reported_currency": ["USD", "USD"],
        }
    )

    unido = unir_estados(balance, resultados)

    assert len(unido) == 2
    assert unido.loc[unido["symbol"] == "AAPL", "net_income"].item() == 10
    assert unido.loc[unido["symbol"] == "MSFT", "net_income"].item() == 20
    # La columna repetida aparece una sola vez, sin sufijos _x / _y.
    assert list(unido.columns).count("reported_currency") == 1


def test_unir_estados_descarta_fechas_sin_pareja():
    balance = pd.DataFrame(
        {"symbol": ["AAPL"] * 2, "date": pd.to_datetime(["2024-12-31", "2025-12-31"])}
    )
    resultados = pd.DataFrame(
        {"symbol": ["AAPL"], "date": pd.to_datetime(["2025-12-31"]), "revenue": [1]}
    )

    assert len(unir_estados(balance, resultados)) == 1


def test_unir_estados_falla_si_hay_duplicados():
    fecha = pd.Timestamp("2025-12-31")
    balance = pd.DataFrame({"symbol": ["AAPL"] * 2, "date": [fecha] * 2})
    resultados = pd.DataFrame({"symbol": ["AAPL"], "date": [fecha]})

    with pytest.raises(pd.errors.MergeError):
        unir_estados(balance, resultados)
