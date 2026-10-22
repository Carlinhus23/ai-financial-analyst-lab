import pytest
import requests

from src.data import fmp_client

CLAVE_FALSA = "clave-que-no-debe-aparecer"


class RespuestaFalsa:
    def __init__(self, status_code, datos=None):
        self.status_code = status_code
        self.ok = status_code < 400
        self._datos = datos

    def json(self):
        return self._datos


@pytest.fixture(autouse=True)
def clave_falsa(monkeypatch):
    # Nunca se usa la clave real ni se llama a FMP.
    monkeypatch.setenv("API_KEY", CLAVE_FALSA)


def test_error_http_no_muestra_la_clave(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: RespuestaFalsa(402))

    with pytest.raises(RuntimeError, match="402") as error:
        fmp_client.get_balance_sheet("XYZ")

    assert CLAVE_FALSA not in str(error.value)
    assert "XYZ" in str(error.value)


def test_fallo_de_conexion_no_muestra_la_clave(monkeypatch):
    def sin_red(*args, **kwargs):
        raise requests.ConnectionError(f"url: /stable?apikey={CLAVE_FALSA}")

    monkeypatch.setattr(requests, "get", sin_red)

    with pytest.raises(RuntimeError, match="No se pudo conectar") as error:
        fmp_client.get_profile("AAPL")

    assert CLAVE_FALSA not in str(error.value)
    assert error.value.__cause__ is None
    assert error.value.__suppress_context__


def test_respuesta_vacia_da_error(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda *a, **k: RespuestaFalsa(200, []))

    with pytest.raises(ValueError, match="no devolvió datos"):
        fmp_client.get_income_statement("XYZ")


def test_respuesta_correcta_devuelve_los_datos(monkeypatch):
    datos = [{"symbol": "AAPL", "date": "2025-09-27"}]
    monkeypatch.setattr(requests, "get", lambda *a, **k: RespuestaFalsa(200, datos))

    assert fmp_client.get_cash_flow_statement("AAPL") == datos
