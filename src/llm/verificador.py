# Comprueba el principio de diseño ("la IA no inventa números") en cada
# respuesta: busca las cifras que escribe la IA y mira si están en la ficha.

import re

# Un número escrito a la española: 2025 · 35,5 · 1.234,56 (sin signo ni %).
NUMERO = re.compile(r"\d+(?:[.,]\d+)*")


def _valor(numero):
    # "1,50" y "1,5" son la misma cifra: se comparan como número, no como texto.
    return float(numero.replace(".", "").replace(",", "."))


def cifras_no_encontradas(texto, ficha):
    # Cifras de la explicación que no aparecen en la ficha, sin repetir y en el
    # orden en que salen. Lista vacía = todas las cifras están en la ficha.
    en_ficha = {_valor(n) for n in NUMERO.findall(ficha)}
    dudosas = [n for n in NUMERO.findall(texto) if _valor(n) not in en_ficha]
    return list(dict.fromkeys(dudosas))
