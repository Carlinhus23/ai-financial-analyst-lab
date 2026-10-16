# Orquesta el motor: une las piezas de src/ en dos operaciones de alto nivel.
# main.py (y más adelante Django) solo llaman a estas funciones.

from src.data.fmp_client import (
    get_balance_sheet,
    get_cash_flow_statement,
    get_income_statement,
)
from src.data.transformer import (
    añadir_trazabilidad,
    estado_a_dataframe,
    unir_estados,
)
from src.data.validator import (
    validar_balance,
    validar_cuenta_resultados,
    validar_flujos_caja,
)
from src.database.duckdb_manager import RUTA_DB, guardar_estado, obtener_estado
from src.financial.ratios import (
    calcular_ratios_balance,
    calcular_ratios_flujos_caja,
    calcular_ratios_rentabilidad,
)

FUENTE = "Financial Modeling Prep"


def actualizar_empresa(symbol, num_periodos=5, ruta_db=RUTA_DB):
    # Descarga, limpia, valida y guarda balance, resultados y flujos de caja.
    # Si algo no valida, se lanza el error antes de guardar nada.
    balance = estado_a_dataframe(get_balance_sheet(symbol, limit=num_periodos))
    balance = añadir_trazabilidad(balance, fuente=FUENTE)
    validar_balance(balance, periodos_esperados=num_periodos)

    resultados = estado_a_dataframe(get_income_statement(symbol, limit=num_periodos))
    resultados = añadir_trazabilidad(resultados, fuente=FUENTE)
    validar_cuenta_resultados(resultados, periodos_esperados=num_periodos)

    flujos = estado_a_dataframe(get_cash_flow_statement(symbol, limit=num_periodos))
    flujos = añadir_trazabilidad(flujos, fuente=FUENTE)
    validar_flujos_caja(flujos, periodos_esperados=num_periodos)

    guardar_estado(balance, "balance_sheet", ruta_db)
    guardar_estado(resultados, "income_statement", ruta_db)
    guardar_estado(flujos, "cash_flow_statement", ruta_db)


def obtener_ratios(symbols=None, ruta_db=RUTA_DB):
    # Lee lo guardado y calcula todos los ratios. No llama a la API.
    balance = obtener_estado("balance_sheet", symbols, ruta_db)
    resultados = obtener_estado("income_statement", symbols, ruta_db)
    flujos = obtener_estado("cash_flow_statement", symbols, ruta_db)

    # El orden importa: en columnas repetidas manda la primera tabla. Los
    # flujos van al final porque su "inventory" es la variación del año, no
    # el saldo del balance que necesita la prueba ácida.
    df = unir_estados(balance, resultados)
    df = unir_estados(df, flujos)
    df = calcular_ratios_balance(df)
    df = calcular_ratios_rentabilidad(df)
    df = calcular_ratios_flujos_caja(df)
    return df
