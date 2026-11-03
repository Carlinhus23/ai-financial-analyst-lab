# Política común: si el denominador es 0 o falta, el ratio no es calculable
# y queda NaN en esa fila; el resto de filas se calcula con normalidad.
#
# Los ratios que mezclan balance y resultados (ROA, ROE) usan el balance de
# cierre del año, no la media entre inicio y fin: es una simplificación.


# Columna de cada ratio y su nombre para mostrar (terminal y web), en el
# orden en que se presentan.
NOMBRES_RATIOS = {
    "deuda_sobre_activos": "Deuda / activos",
    "deuda_sobre_patrimonio": "Deuda / patrimonio",
    "liquidez_corriente": "Liquidez corriente",
    "prueba_acida": "Prueba ácida",
    "ratio_caja": "Ratio de caja",
    "margen_bruto": "Margen bruto",
    "margen_operativo": "Margen operativo",
    "margen_neto": "Margen neto",
    "roa": "ROA",
    "roe": "ROE",
    "margen_fcf": "Margen FCF",
    "calidad_beneficio": "Calidad del beneficio",
}


def _dividir(numerador, denominador):
    return numerador / denominador.where(denominador != 0)


def _dividir_si_positivo(numerador, denominador):
    # Para el patrimonio: si es negativo, el ratio sale negativo y no
    # significa "poca deuda" o "poca rentabilidad", sino que no es
    # interpretable. Por eso también es NaN cuando el denominador es <= 0.
    return numerador / denominador.where(denominador > 0)


# --- Balance: endeudamiento y liquidez ---


def calcular_deuda_sobre_activos(df):
    df_resultado = df.copy()
    df_resultado["deuda_sobre_activos"] = _dividir(
        df_resultado["total_debt"],
        df_resultado["total_assets"],
    )
    return df_resultado


def calcular_deuda_sobre_patrimonio(df):
    df_resultado = df.copy()
    df_resultado["deuda_sobre_patrimonio"] = _dividir_si_positivo(
        df_resultado["total_debt"],
        df_resultado["total_stockholders_equity"],
    )
    return df_resultado


def calcular_liquidez_corriente(df):
    df_resultado = df.copy()
    df_resultado["liquidez_corriente"] = _dividir(
        df_resultado["total_current_assets"],
        df_resultado["total_current_liabilities"],
    )
    return df_resultado


def calcular_prueba_acida(df):
    # Como la liquidez corriente, pero sin inventario (el activo corriente
    # más difícil de convertir en caja).
    df_resultado = df.copy()
    df_resultado["prueba_acida"] = _dividir(
        df_resultado["total_current_assets"] - df_resultado["inventory"],
        df_resultado["total_current_liabilities"],
    )
    return df_resultado


def calcular_ratio_caja(df):
    df_resultado = df.copy()
    df_resultado["ratio_caja"] = _dividir(
        df_resultado["cash_and_cash_equivalents"],
        df_resultado["total_current_liabilities"],
    )
    return df_resultado


# --- Cuenta de resultados: márgenes ---


def calcular_margenes(df):
    df_resultado = df.copy()
    ingresos = df_resultado["revenue"]
    df_resultado["margen_bruto"] = _dividir(df_resultado["gross_profit"], ingresos)
    df_resultado["margen_operativo"] = _dividir(
        df_resultado["operating_income"], ingresos
    )
    df_resultado["margen_neto"] = _dividir(df_resultado["net_income"], ingresos)
    return df_resultado


# --- Balance + resultados: rentabilidad ---


def calcular_roa(df):
    df_resultado = df.copy()
    df_resultado["roa"] = _dividir(
        df_resultado["net_income"],
        df_resultado["total_assets"],
    )
    return df_resultado


def calcular_roe(df):
    df_resultado = df.copy()
    df_resultado["roe"] = _dividir_si_positivo(
        df_resultado["net_income"],
        df_resultado["total_stockholders_equity"],
    )
    return df_resultado


# --- Flujos de caja ---


def calcular_flujo_caja_libre(df):
    # Lo calculamos nosotros: la SEC no da el FCF. El capex llega en negativo
    # (el validador lo comprueba).
    df_resultado = df.copy()
    df_resultado["flujo_caja_libre"] = (
        df_resultado["operating_cash_flow"] + df_resultado["capital_expenditure"]
    )
    return df_resultado


def calcular_margen_fcf(df):
    df_resultado = calcular_flujo_caja_libre(df)
    df_resultado["margen_fcf"] = _dividir(
        df_resultado["flujo_caja_libre"],
        df_resultado["revenue"],
    )
    return df_resultado


def calcular_calidad_beneficio(df):
    # Caja operativa por cada euro de beneficio. Con pérdidas el ratio cambia
    # de signo y deja de ser interpretable, así que es NaN si el beneficio <= 0.
    df_resultado = df.copy()
    df_resultado["calidad_beneficio"] = _dividir_si_positivo(
        df_resultado["operating_cash_flow"],
        df_resultado["net_income"],
    )
    return df_resultado


# --- Valoración (mercado) ---


def calcular_per(capitalizacion, beneficio_neto):
    # PER = capitalización bursátil actual / beneficio neto del último
    # ejercicio. Equivale a precio / BPA sin depender del número de acciones.
    # Con beneficio <= 0 (o vacío) no es interpretable: NaN.
    if not beneficio_neto > 0:
        return float("nan")
    return capitalizacion / beneficio_neto


# --- Agrupadores ---


def _aplicar(df, funciones):
    df_resultado = df
    for calcular in funciones:
        df_resultado = calcular(df_resultado)
    return df_resultado


def calcular_ratios_balance(df):
    return _aplicar(
        df,
        [
            calcular_deuda_sobre_activos,
            calcular_deuda_sobre_patrimonio,
            calcular_liquidez_corriente,
            calcular_prueba_acida,
            calcular_ratio_caja,
        ],
    )


def calcular_ratios_rentabilidad(df):
    # Necesita balance y cuenta de resultados unidos (ver obtener_datos_analisis).
    return _aplicar(df, [calcular_margenes, calcular_roa, calcular_roe])


def calcular_ratios_flujos_caja(df):
    # Necesita flujos de caja y cuenta de resultados unidos (usa revenue).
    return _aplicar(df, [calcular_margen_fcf, calcular_calidad_beneficio])
