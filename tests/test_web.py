import pytest

from src import pipeline


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


def test_pagina_empresa_acepta_minusculas(client, db_con_aapl):
    assert client.get("/empresa/aapl/").status_code == 200


def test_empresa_sin_datos_da_404(client, db_con_aapl):
    assert client.get("/empresa/MSFT/").status_code == 404
