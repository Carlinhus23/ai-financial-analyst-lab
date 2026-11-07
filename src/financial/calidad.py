# Calidad de datos: por qué un ratio sale "—" (NaN). No calcula ratios: mira
# los que ya calculó ratios.py y busca la causa en las partidas de las que
# depende cada uno.

import math

from src.financial.ratios import NOMBRES_RATIOS

# Partidas (columnas de la base) que usa cada ratio. Si falta una, el ratio
# no se puede calcular. Hay un test que comprueba que no falta ningún ratio.
ENTRADAS_RATIOS = {
    "deuda_sobre_activos": ["total_debt", "total_assets"],
    "deuda_sobre_patrimonio": ["total_debt", "total_stockholders_equity"],
    "liquidez_corriente": ["total_current_assets", "total_current_liabilities"],
    "prueba_acida": ["total_current_assets", "inventory", "total_current_liabilities"],
    "ratio_caja": ["cash_and_cash_equivalents", "total_current_liabilities"],
    "margen_bruto": ["gross_profit", "revenue"],
    "margen_operativo": ["operating_income", "revenue"],
    "margen_neto": ["net_income", "revenue"],
    "roa": ["net_income", "total_assets"],
    "roe": ["net_income", "total_stockholders_equity"],
    "rotacion_activos": ["revenue", "total_assets"],
    "dias_inventario": ["inventory", "revenue", "gross_profit"],
    "margen_fcf": ["operating_cash_flow", "capital_expenditure", "revenue"],
    "calidad_beneficio": ["operating_cash_flow", "net_income"],
    "crecimiento_ventas": ["revenue"],
    "crecimiento_beneficio": ["net_income"],
}

NOMBRES_PARTIDAS = {
    "total_debt": "deuda",
    "total_assets": "activo total",
    "total_stockholders_equity": "patrimonio neto",
    "total_current_assets": "activo corriente",
    "total_current_liabilities": "pasivo corriente",
    "inventory": "inventario",
    "cash_and_cash_equivalents": "caja",
    "gross_profit": "beneficio bruto",
    "operating_income": "resultado operativo",
    "net_income": "beneficio neto",
    "revenue": "ventas",
    "operating_cash_flow": "flujo de caja operativo",
    "capital_expenditure": "capex",
}

# Cuando no falta ninguna partida, el "—" lo pone una regla de ratios.py.
MOTIVOS_REGLA = {
    "deuda_sobre_patrimonio": "Patrimonio neto 0 o negativo",
    "roe": "Patrimonio neto 0 o negativo",
    "calidad_beneficio": "Beneficio neto 0 o negativo",
    "dias_inventario": "Coste de ventas 0 o negativo",
    "crecimiento_ventas": "Falta el año anterior o sus ventas son 0",
    "crecimiento_beneficio": "Falta el año anterior o su beneficio era 0 o negativo",
}


def _motivo(fila, columna):
    faltan = [
        NOMBRES_PARTIDAS[c] for c in ENTRADAS_RATIOS[columna] if math.isnan(fila[c])
    ]
    if faltan:
        return "Falta en la SEC: " + ", ".join(faltan)
    return MOTIVOS_REGLA.get(columna, "Divisor 0")


def ratios_sin_dato(ratios):
    # Recibe la tabla de obtener_ratios y devuelve una fila por (empresa,
    # ratio, motivo) con los años afectados. El crecimiento del primer año de
    # cada empresa no cuenta: nunca tiene año anterior, no es un fallo.
    grupos = {}
    vistas = set()
    for fila in ratios.to_dict("records"):
        primer_año = fila["symbol"] not in vistas
        vistas.add(fila["symbol"])
        for columna in NOMBRES_RATIOS:
            if not math.isnan(fila[columna]):
                continue
            if primer_año and columna.startswith("crecimiento"):
                continue
            clave = (fila["symbol"], columna, _motivo(fila, columna))
            grupos.setdefault(clave, []).append(fila["fiscal_year"])

    return [
        {
            "symbol": symbol,
            "ratio": NOMBRES_RATIOS[columna],
            "motivo": motivo,
            "años": ", ".join(años),
        }
        for (symbol, columna, motivo), años in grupos.items()
    ]
