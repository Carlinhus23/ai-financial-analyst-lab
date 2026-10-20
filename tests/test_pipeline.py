import pytest

from src import pipeline


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


def test_perfil_guardado_con_per(api_falsa, tmp_path):
    ruta_db = str(tmp_path / "test.duckdb")

    pipeline.actualizar_empresa("AAPL", num_periodos=1, ruta_db=ruta_db)
    perfil = pipeline.obtener_perfil("AAPL", ruta_db=ruta_db)

    assert perfil["company_name"] == "Apple Inc."
    assert perfil["sector"] == "Technology"
    assert perfil["per"] == pytest.approx(20)  # 2400 / 120


def test_si_no_valida_no_guarda_nada(api_falsa, tmp_path):
    ruta_db = str(tmp_path / "test.duckdb")

    # Pedimos 5 periodos pero la "API" solo devuelve 1: la validación falla.
    with pytest.raises(ValueError, match="Se esperaban 5"):
        pipeline.actualizar_empresa("AAPL", num_periodos=5, ruta_db=ruta_db)

    assert not (tmp_path / "test.duckdb").exists()
