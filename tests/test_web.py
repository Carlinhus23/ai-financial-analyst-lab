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


def test_inicio_muestra_una_tarjeta_con_las_cifras_clave(client, db_con_aapl):
    texto = client.get("/").text

    assert "Technology" in texto  # sector en la tarjeta
    assert "Apple Inc." in texto
    assert "150,50 USD" in texto  # precio
    assert "20,00" in texto  # PER


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
    assert "<em>Mediana</em>" not in texto  # una sola empresa en su sector


def test_comparar_anade_la_mediana_al_final_de_cada_sector(
    client, db_con_aapl, monkeypatch
):
    def empresa(symbol, per):
        fila = {columna: float("nan") for columna in views.NOMBRES_RATIOS}
        return {
            **fila,
            "symbol": symbol,
            "sector": "Tech",
            "fiscal_year": "2025",
            "per": per,
        }

    datos = [empresa("AAPL", 20.0), empresa("MSFT", 30.0)]
    monkeypatch.setattr(views, "obtener_comparacion", lambda ruta: datos)

    texto = client.get("/comparar/").text

    assert "<em>Mediana</em>" in texto
    assert "<em>25,00</em>" in texto  # mediana del PER de 20 y 30
    assert texto.index("/empresa/MSFT/") < texto.index("<em>Mediana</em>")


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
        views, "explicar_empresa", lambda s, r: ("La deuda es baja.", "gemini-x", [])
    )

    texto = client.get("/empresa/AAPL/?explicar=1").text

    assert "Explicación de la IA" in texto
    assert "La deuda es baja." in texto
    assert "gemini-x" in texto
    assert "Comprobado: todas las cifras" in texto


def test_avisa_si_la_ia_escribe_cifras_que_no_estan_en_la_ficha(
    client, db_con_aapl, monkeypatch
):
    monkeypatch.setattr(
        views,
        "explicar_empresa",
        lambda s, r: ("La deuda sube un 99,9 %.", "gemini-x", ["99,9"]),
    )

    texto = client.get("/empresa/AAPL/?explicar=1").text

    assert "no están en la ficha: 99,9" in texto
    assert "Comprobado" not in texto


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


def test_minigrafico_pone_el_minimo_abajo_y_el_maximo_arriba():
    # 3 años en 100 px de ancho (x = 0, 50, 100) y 24 de alto (y = 24 abajo).
    assert views._minigrafico([0.1, 0.3, 0.2]) == "0.0,24.0 50.0,0.0 100.0,12.0"


def test_minigrafico_salta_los_años_sin_dato():
    nan = float("nan")

    assert views._minigrafico([0.1, nan, 0.3]) == "0.0,24.0 100.0,0.0"


def test_minigrafico_vacio_si_hay_menos_de_dos_datos():
    nan = float("nan")

    assert views._minigrafico([0.5]) == ""
    assert views._minigrafico([nan, 0.5, nan]) == ""


def test_millones_con_punto_de_miles_y_raya_si_falta():
    assert views._millones(391_035_000_000) == "391.035"
    assert views._millones(-1_234_000_000) == "-1.234"
    assert views._millones(float("nan")) == "—"


def test_pagina_empresa_muestra_los_estados_financieros(client, db_con_aapl):
    texto = client.get("/empresa/AAPL/").text

    assert "Estados financieros (millones de USD)" in texto
    for partida in ["Activo total", "Ventas", "Flujo de caja libre (calculado)"]:
        assert partida in texto


def test_pagina_empresa_tiene_columna_de_evolucion(client, db_con_aapl):
    # Con un solo ejercicio no hay línea que dibujar, pero la página no falla.
    texto = client.get("/empresa/AAPL/").text

    assert "Evolución" in texto
    assert "<polyline" not in texto


def test_pagina_empresa_enlaza_los_10k_de_la_sec(client, db_con_aapl):
    texto = client.get("/empresa/AAPL/").text

    assert "ver los 10-K originales en la SEC" in texto
    assert "browse-edgar?action=getcompany&amp;CIK=AAPL&amp;type=10-K" in texto


def _empresas_falsas(monkeypatch, pers):
    # Empresas del mismo sector con estos PER y el resto de ratios vacíos.
    datos = []
    for symbol, per in pers.items():
        fila = {columna: float("nan") for columna in views.NOMBRES_RATIOS}
        datos.append(
            {
                **fila,
                "symbol": symbol,
                "sector": "Tech",
                "fiscal_year": "2025",
                "per": per,
            }
        )
    monkeypatch.setattr(views, "obtener_comparacion", lambda ruta: datos)


def test_comparar_ordena_de_mayor_a_menor_con_los_vacios_al_final(
    client, db_con_aapl, monkeypatch
):
    _empresas_falsas(monkeypatch, {"AAPL": 20.0, "NVDA": float("nan"), "MSFT": 30.0})

    texto = client.get("/comparar/?orden=per").text

    posiciones = [texto.index(f"/empresa/{s}/") for s in ["MSFT", "AAPL", "NVDA"]]
    assert posiciones == sorted(posiciones)
    assert texto.index("/empresa/NVDA/") < texto.index("<em>Mediana</em>")
    assert "PER</a> ▼" in texto


def test_comparar_ignora_un_orden_desconocido(client, db_con_aapl, monkeypatch):
    _empresas_falsas(monkeypatch, {"AAPL": 20.0, "MSFT": 30.0})

    respuesta = client.get("/comparar/?orden=no_existe")

    assert respuesta.status_code == 200
    assert respuesta.text.index("/empresa/AAPL/") < respuesta.text.index(
        "/empresa/MSFT/"
    )
    assert "▼" not in respuesta.text


def test_csv_descarga_los_ratios_listos_para_excel(client, db_con_aapl):
    respuesta = client.get("/empresa/AAPL/csv/")

    assert respuesta.status_code == 200
    assert respuesta["Content-Type"].startswith("text/csv")
    assert 'filename="AAPL_ratios.csv"' in respuesta["Content-Disposition"]
    texto = respuesta.content.decode("utf-8")
    cabecera, fila = texto.lstrip("﻿").splitlines()[:2]
    assert texto.startswith("﻿")  # Excel lee bien las tildes
    assert cabecera.startswith("Ejercicio;Deuda / activos;")
    assert "0,2500" in fila  # deuda / activos = 100 / 400
    assert "1,5000" in fila  # liquidez corriente = 150 / 100


def test_csv_de_empresa_sin_datos_da_404(client, db_con_aapl):
    assert client.get("/empresa/MSFT/csv/").status_code == 404


def test_pagina_empresa_enlaza_el_csv(client, db_con_aapl):
    assert "/empresa/AAPL/csv/" in client.get("/empresa/AAPL/").text


def test_pagina_empresa_agrupa_los_ratios_en_bloques(client, db_con_aapl):
    texto = client.get("/empresa/AAPL/").text

    posiciones = [
        texto.index(f">{grupo}</th>")
        for grupo in ["Endeudamiento", "Liquidez", "Rentabilidad", "Crecimiento"]
    ]
    assert posiciones == sorted(posiciones)
    assert texto.index(">Endeudamiento</th>") < texto.index("Deuda / activos")
