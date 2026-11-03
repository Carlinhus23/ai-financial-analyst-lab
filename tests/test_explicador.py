import pytest
import requests

from src.llm import explicador

CLAVE_FALSA = "clave-que-no-debe-aparecer"


class RespuestaFalsa:
    def __init__(self, status_code, texto=None):
        self.status_code = status_code
        self.ok = status_code < 400
        self._texto = texto

    def json(self):
        return {"candidates": [{"content": {"parts": [{"text": self._texto}]}}]}


@pytest.fixture
def gemini_falso(monkeypatch):
    # Nunca se usa la clave real ni se llama a Gemini. Devuelve, en orden, las
    # respuestas de la lista y apunta a qué direcciones y con qué cabeceras se
    # ha llamado.
    monkeypatch.setenv("GEMINI_API_KEY", CLAVE_FALSA)
    llamadas = []
    respuestas = []

    def post_falso(url, headers, json, timeout):
        llamadas.append({"url": url, "headers": headers, "json": json})
        return respuestas.pop(0)

    monkeypatch.setattr(requests, "post", post_falso)
    return llamadas, respuestas


def test_devuelve_la_explicacion_y_envia_la_ficha(gemini_falso):
    llamadas, respuestas = gemini_falso
    respuestas.append(RespuestaFalsa(200, "La deuda baja."))

    texto, modelo = explicador.explicar("Deuda / activos: 2025: 25,0 %")

    assert texto == "La deuda baja."
    assert modelo == explicador.MODELOS[0]
    peticion = llamadas[0]["json"]
    assert (
        peticion["contents"][0]["parts"][0]["text"] == "Deuda / activos: 2025: 25,0 %"
    )
    assert "No calcules" in peticion["system_instruction"]["parts"][0]["text"]


def test_la_clave_va_en_la_cabecera_y_no_en_la_url(gemini_falso):
    llamadas, respuestas = gemini_falso
    respuestas.append(RespuestaFalsa(200, "ok"))

    explicador.explicar("ficha")

    assert llamadas[0]["headers"]["x-goog-api-key"] == CLAVE_FALSA
    assert CLAVE_FALSA not in llamadas[0]["url"]


def test_si_un_modelo_esta_saturado_prueba_el_siguiente(gemini_falso):
    llamadas, respuestas = gemini_falso
    respuestas.extend([RespuestaFalsa(503), RespuestaFalsa(200, "ok")])

    assert explicador.explicar("ficha") == ("ok", explicador.MODELOS[1])
    assert explicador.MODELOS[0] in llamadas[0]["url"]
    assert explicador.MODELOS[1] in llamadas[1]["url"]


def test_si_todos_estan_saturados_avisa(gemini_falso):
    _, respuestas = gemini_falso
    respuestas.extend([RespuestaFalsa(503)] * len(explicador.MODELOS))

    with pytest.raises(RuntimeError, match="saturado"):
        explicador.explicar("ficha")


def test_otro_error_de_gemini_no_muestra_la_clave(gemini_falso):
    _, respuestas = gemini_falso
    respuestas.append(RespuestaFalsa(400))

    with pytest.raises(RuntimeError, match="400") as error:
        explicador.explicar("ficha")

    assert CLAVE_FALSA not in str(error.value)


def test_sin_clave_avisa(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        explicador.explicar("ficha")


def test_si_un_modelo_tarda_demasiado_prueba_el_siguiente(gemini_falso, monkeypatch):
    llamadas, _ = gemini_falso
    respuestas = [requests.Timeout(), RespuestaFalsa(200, "ok")]

    def post_lento(url, headers, json, timeout):
        llamadas.append({"url": url})
        respuesta = respuestas.pop(0)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    monkeypatch.setattr(requests, "post", post_lento)

    assert explicador.explicar("ficha") == ("ok", explicador.MODELOS[1])
