import pytest

from src import pipeline
from web import views


@pytest.fixture
def db_con_aapl(api_falsa, tmp_path, settings):
    # DuckDB temporal con AAPL (datos falsos) y Django apuntando a ella.
    ruta = tmp_path / "test.duckdb"
    pipeline.actualizar_empresa("AAPL", num_periodos=1, ruta_db=str(ruta))
    settings.RUTA_DUCKDB = ruta
    return ruta


def test_inicio_lista_las_empresas_guardadas(client, db_con_aapl):
    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert "AAPL" in respuesta.text
    assert "/empresa/AAPL/" in respuesta.text


def test_inicio_sin_base_de_datos_avisa_y_no_la_crea(client, tmp_path, settings):
    settings.RUTA_DUCKDB = tmp_path / "no_existe.duckdb"

    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert "python main.py" in respuesta.text
    assert not settings.RUTA_DUCKDB.exists()


def test_pagina_empresa_muestra_los_ratios(client, db_con_aapl):
    respuesta = client.get("/empresa/AAPL/")

    assert respuesta.status_code == 200
    texto = respuesta.text
    assert "Deuda / activos" in texto
    assert "25,0 %" in texto  # deuda / activos = 100 / 400
    assert "1,50" in texto  # liquidez corriente = 150 / 100
    assert "Margen FCF" in texto


def test_pagina_empresa_muestra_perfil_y_per(client, db_con_aapl):
    texto = client.get("/empresa/AAPL/").text

    assert "Apple Inc." in texto
    assert "150,50 USD" in texto
    assert "-0,15 %" in texto
    assert "PER: <strong>20,00</strong>" in texto
    assert "finance.yahoo.com/quote/AAPL/news" in texto


def test_comparar_muestra_una_fila_por_empresa(client, db_con_aapl):
    respuesta = client.get("/comparar/")

    assert respuesta.status_code == 200
    texto = respuesta.text
    assert "/empresa/AAPL/" in texto
    assert "Technology" in texto
    assert "20,00" in texto  # PER
    assert "25,0 %" in texto  # deuda / activos


def test_comparar_sin_base_de_datos_avisa(client, tmp_path, settings):
    settings.RUTA_DUCKDB = tmp_path / "no_existe.duckdb"

    respuesta = client.get("/comparar/")

    assert respuesta.status_code == 200
    assert "python main.py" in respuesta.text


def test_datos_que_faltan_en_la_fuente_salen_como_raya(
    api_falsa, monkeypatch, client, tmp_path, settings
):
    # Como Exxon en la SEC: sin beneficio bruto ni resultado operativo.
    sin_datos = [
        {
            "date": "2025-09-27",
            "symbol": "AAPL",
            "reportedCurrency": "USD",
            "fiscalYear": "2025",
            "revenue": 500,
            "grossProfit": float("nan"),
            "operatingIncome": float("nan"),
            "netIncome": 120,
        }
    ]
    monkeypatch.setattr(pipeline, "get_income_statement", lambda s, limit: sin_datos)
    ruta = tmp_path / "test.duckdb"
    pipeline.actualizar_empresa("AAPL", num_periodos=1, ruta_db=str(ruta))
    settings.RUTA_DUCKDB = ruta

    for direccion in ["/empresa/AAPL/", "/comparar/"]:
        respuesta = client.get(direccion)
        assert respuesta.status_code == 200
        assert "—" in respuesta.text


def test_empresa_muestra_el_boton_de_ia_sin_llamar_a_gemini(
    client, db_con_aapl, monkeypatch
):
    def no_llamar(*args):
        raise AssertionError("No se debe llamar a la IA sin pulsar el botón")

    monkeypatch.setattr(views, "explicar_empresa", no_llamar)

    texto = client.get("/empresa/AAPL/").text

    assert "Explicar con IA" in texto


def test_al_pulsar_el_boton_muestra_la_explicacion(client, db_con_aapl, monkeypatch):
    monkeypatch.setattr(
        views, "explicar_empresa", lambda s, r: ("La deuda es baja.", "gemini-x")
    )

    texto = client.get("/empresa/AAPL/?explicar=1").text

    assert "Explicación de la IA" in texto
    assert "La deuda es baja." in texto
    assert "gemini-x" in texto


def test_si_falla_la_ia_la_pagina_sigue_funcionando(client, db_con_aapl, monkeypatch):
    def falla(*args):
        raise RuntimeError("Gemini está saturado ahora mismo.")

    monkeypatch.setattr(views, "explicar_empresa", falla)

    respuesta = client.get("/empresa/AAPL/?explicar=1")

    assert respuesta.status_code == 200
    assert "No se pudo generar la explicación" in respuesta.text
    assert "Deuda / activos" in respuesta.text


def test_pagina_empresa_acepta_minusculas(client, db_con_aapl):
    assert client.get("/empresa/aapl/").status_code == 200


def test_empresa_sin_datos_da_404(client, db_con_aapl):
    assert client.get("/empresa/MSFT/").status_code == 404
