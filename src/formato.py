# Cómo se escribe cada cifra para una persona (web y explicación de la IA).
# Es solo presentación: las cifras llegan ya calculadas desde ratios.py.
# Estar en un solo sitio garantiza que la IA lee lo mismo que se ve en la web.

import math

RATIOS_EN_PORCENTAJE = {
    "deuda_sobre_activos",
    "margen_bruto",
    "margen_operativo",
    "margen_neto",
    "roa",
    "roe",
    "margen_fcf",
    "crecimiento_ventas",
    "crecimiento_beneficio",
}


def formatear(columna, valor):
    if valor is None or math.isnan(valor):
        return "—"
    if columna in RATIOS_EN_PORCENTAJE:
        return f"{valor * 100:.1f} %".replace(".", ",")
    return f"{valor:.2f}".replace(".", ",")
