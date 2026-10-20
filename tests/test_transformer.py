import pandas as pd

from src.data.transformer import (
    añadir_trazabilidad,
    convertir_a_snake_case,
    estado_a_dataframe,
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


def test_estado_a_dataframe_sin_date_no_falla():
    # El perfil de FMP no trae "date".
    df = estado_a_dataframe([{"symbol": "AAPL", "marketCap": 2400}])

    assert list(df.columns) == ["symbol", "market_cap"]
