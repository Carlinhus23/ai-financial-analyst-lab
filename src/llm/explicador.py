# Capa de IA: Gemini (plan gratuito de la API) explica ratios que ya ha
# calculado ratios.py. Nunca calcula ni inventa cifras: solo recibe la ficha
# de la empresa ya escrita (ver docs/decisiones.md, decisiones 1 y 5).

import os

import requests
from dotenv import load_dotenv

load_dotenv()

URL = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"

# Por orden de preferencia. En el plan gratuito un modelo puede estar
# saturado (error 503), llegar a su límite (429) o tardar demasiado: entonces
# se prueba el siguiente. Flash-Lite va primero porque casi siempre responde y
# en 2-3 s (medido el 03-11-2026: los Flash grandes daban 503 a menudo).
MODELOS = ["gemini-3.1-flash-lite", "gemini-3.8-flash"]
CODIGOS_SATURADO = {429, 503}
ESPERA_MAXIMA = 20  # segundos por modelo

INSTRUCCIONES = """Eres un analista financiero que explica, en español, los ratios
de una empresa a alguien sin formación financiera.
Reglas:
- Usa SOLO las cifras de la ficha. No calcules cifras nuevas (ni diferencias
  ni medias) y no inventes datos.
- Explica qué mide cada grupo de ratios y si sube, baja o se mantiene en los
  años de la ficha.
- Si un dato aparece como "—", di que no está disponible y no lo estimes.
- No digas que un ratio es alto o bajo en general: depende del sector.
- No des recomendaciones de inversión.
- Como máximo 5 párrafos cortos, en texto plano, sin asteriscos ni listas."""


def explicar(ficha):
    # Recibe la ficha de la empresa (texto con las cifras ya calculadas) y
    # devuelve la explicación de Gemini y el modelo que la ha escrito.
    clave = os.getenv("GEMINI_API_KEY")
    if not clave:
        raise RuntimeError("Falta GEMINI_API_KEY en .env (clave de Google AI Studio).")

    peticion = {
        "system_instruction": {"parts": [{"text": INSTRUCCIONES}]},
        "contents": [{"role": "user", "parts": [{"text": ficha}]}],
    }
    for modelo in MODELOS:
        # La clave va en una cabecera, no en la URL: así nunca sale en un error.
        try:
            response = requests.post(
                URL.format(modelo=modelo),
                headers={"x-goog-api-key": clave},
                json=peticion,
                timeout=ESPERA_MAXIMA,
            )
        except requests.Timeout:
            continue
        except requests.RequestException as error:
            raise RuntimeError(
                f"No se pudo conectar con Gemini ({type(error).__name__})."
            ) from None

        if response.status_code in CODIGOS_SATURADO:
            continue
        if not response.ok:
            raise RuntimeError(f"Gemini respondió {response.status_code}.")
        texto = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return texto, modelo

    raise RuntimeError("Gemini está saturado ahora mismo. Prueba en unos minutos.")
