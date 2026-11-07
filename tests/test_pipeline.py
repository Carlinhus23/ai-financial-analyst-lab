import conftest
import pytest

from src import pipeline


def test_pipeline_completo_sin_api(api_falsa, tmp_path):
    ruta_db = str(tmp_path / "test.duckdb")

    pipeline.actualizar_empresa("AAPL", num_periodos=1, ruta_db=ruta_db)
    ratios = pipeline.obtener_ratios(["AAPL"], ruta_db=ruta_db)

    fila = ratios.iloc[0]
    assert fila["symbol"] == "AAPL"
    assert fila["fuente"] == "SEC EDGAR (10-K)"
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
    assert perfil["fuente"] == "Yahoo Finance"
    assert perfil["per"] == pytest.approx(20)  # 2400 / 120


def test_comparacion_una_fila_por_empresa_con_sector_y_per(api_falsa, tmp_path):
    ruta_db = str(tmp_path / "test.duckdb")
    pipeline.actualizar_empresa("AAPL", num_periodos=1, ruta_db=ruta_db)

    filas = pipeline.obtener_comparacion(ruta_db=ruta_db)

    assert len(filas) == 1
    assert filas[0]["symbol"] == "AAPL"
    assert filas[0]["sector"] == "Technology"
    assert filas[0]["per"] == pytest.approx(20)
    assert filas[0]["deuda_sobre_activos"] == pytest.approx(0.25)


def test_comparacion_sin_sector_no_falla(api_falsa, monkeypatch, tmp_path):
    # Yahoo puede no dar el sector (None): no debe romper la ordenación.
    sin_sector = [conftest.PERFIL_FALSO[0] | {"sector": None}]
    monkeypatch.setattr(pipeline, "get_profile", lambda s: sin_sector)
    ruta_db = str(tmp_path / "test.duckdb")
    pipeline.actualizar_empresa("AAPL", num_periodos=1, ruta_db=ruta_db)

    filas = pipeline.obtener_comparacion(ruta_db=ruta_db)

    assert filas[0]["sector"] == "—"
    assert filas[0]["per"] == pytest.approx(20)


def test_ficha_empresa_lleva_las_cifras_como_en_la_web(api_falsa, tmp_path):
    ruta_db = str(tmp_path / "test.duckdb")
    pipeline.actualizar_empresa("AAPL", num_periodos=1, ruta_db=ruta_db)

    ficha = pipeline.ficha_empresa("AAPL", ruta_db=ruta_db)

    assert "Empresa: AAPL (Apple Inc.). Sector: Technology. PER: 20,00." in ficha
    assert "Deuda / activos: 2025: 25,0 %" in ficha
    assert "Liquidez corriente: 2025: 1,50" in ficha


def test_explicar_empresa_solo_envia_la_ficha(api_falsa, monkeypatch, tmp_path):
    ruta_db = str(tmp_path / "test.duckdb")
    pipeline.actualizar_empresa("AAPL", num_periodos=1, ruta_db=ruta_db)
    recibido = []

    def explicar_falso(ficha, instrucciones=None):
        recibido.append(ficha)
        return "La deuda es el 25,0 % y sube un 99,9 %.", "gemini-x"

    monkeypatch.setattr(pipeline, "explicar", explicar_falso)

    texto, modelo, dudosas = pipeline.explicar_empresa("AAPL", ruta_db=ruta_db)

    assert recibido == [pipeline.ficha_empresa("AAPL", ruta_db=ruta_db)]
    assert modelo == "gemini-x"
    assert dudosas == ["99,9"]  # 25,0 % sí está en la ficha; 99,9 no


def test_si_no_valida_no_guarda_nada(api_falsa, tmp_path):
    ruta_db = str(tmp_path / "test.duckdb")

    # Pedimos 5 periodos pero la "API" solo devuelve 1: la validación falla.
    with pytest.raises(ValueError, match="Se esperaban 5"):
        pipeline.actualizar_empresa("AAPL", num_periodos=5, ruta_db=ruta_db)

    assert not (tmp_path / "test.duckdb").exists()


def test_la_segunda_explicacion_de_la_misma_ficha_no_llama_a_gemini(
    api_falsa, monkeypatch, tmp_path
):
    ruta_db = str(tmp_path / "test.duckdb")
    pipeline.actualizar_empresa("AAPL", num_periodos=1, ruta_db=ruta_db)
    llamadas = []

    def explicar_falso(ficha, instrucciones=None):
        llamadas.append(ficha)
        return "La deuda es el 25,0 %.", "gemini-x"

    monkeypatch.setattr(pipeline, "explicar", explicar_falso)

    primera = pipeline.explicar_empresa("AAPL", ruta_db=ruta_db)
    segunda = pipeline.explicar_empresa("AAPL", ruta_db=ruta_db)

    assert len(llamadas) == 1
    assert segunda[0] == primera[0]
    assert segunda[1].startswith("gemini-x, guardada el ")
    assert segunda[2] == []  # el verificador también revisa la guardada


def test_comparar_empresas_envia_las_dos_fichas_con_sus_instrucciones(
    monkeypatch, tmp_path
):
    ruta_db = str(tmp_path / "test.duckdb")
    fichas = {
        "AAPL": "Deuda / activos: 2025: 25,0 %",
        "KO": "Deuda / activos: 2025: 43,4 %",
    }
    monkeypatch.setattr(pipeline, "ficha_empresa", lambda s, r: fichas[s])
    recibido = []

    def explicar_falso(ficha, instrucciones):
        recibido.append((ficha, instrucciones))
        return "KO tiene más deuda (43,4 %) que AAPL (25,0 %), un 18,4 % más.", "x"

    monkeypatch.setattr(pipeline, "explicar", explicar_falso)

    texto, modelo, dudosas = pipeline.comparar_empresas("AAPL", "KO", ruta_db)

    ficha, instrucciones = recibido[0]
    assert fichas["AAPL"] in ficha and fichas["KO"] in ficha
    assert instrucciones == pipeline.INSTRUCCIONES_COMPARAR
    # 25,0 y 43,4 están en las fichas; 18,4 es una resta que la IA no debía hacer.
    assert dudosas == ["18,4"]
    # La segunda vez sale guardada (clave "AAPL+KO"), sin llamar a Gemini.
    pipeline.comparar_empresas("AAPL", "KO", ruta_db)
    assert len(recibido) == 1


def test_con_nueva_vuelve_a_llamar_a_gemini_y_guarda_la_nueva(
    api_falsa, monkeypatch, tmp_path
):
    ruta_db = str(tmp_path / "test.duckdb")
    pipeline.actualizar_empresa("AAPL", num_periodos=1, ruta_db=ruta_db)
    respuestas = iter(["Primera.", "Segunda."])
    monkeypatch.setattr(pipeline, "explicar", lambda f, i: (next(respuestas), "x"))

    pipeline.explicar_empresa("AAPL", ruta_db=ruta_db)
    nueva = pipeline.explicar_empresa("AAPL", ruta_db=ruta_db, nueva=True)
    despues = pipeline.explicar_empresa("AAPL", ruta_db=ruta_db)

    assert nueva[0] == "Segunda."
    assert despues[0] == "Segunda."  # la guardada ahora es la nueva
