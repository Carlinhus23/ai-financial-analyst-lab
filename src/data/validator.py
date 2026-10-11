COLUMNAS_BALANCE = [
    "symbol",
    "date",
    "total_assets",
    "total_debt",
    "cash_and_cash_equivalents",
    "net_debt",
]

COLUMNAS_RESULTADOS = [
    "symbol",
    "date",
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
]


def _validar_comun(df, columnas_obligatorias, periodos_esperados):
    # Comprobaciones que valen para cualquier estado financiero.
    if df.empty:
        raise ValueError("El estado financiero está vacío.")

    faltan = [c for c in columnas_obligatorias if c not in df.columns]
    if faltan:
        raise ValueError(f"Faltan columnas obligatorias: {faltan}")

    if periodos_esperados is not None and len(df) != periodos_esperados:
        raise ValueError(f"Se esperaban {periodos_esperados} periodos y hay {len(df)}.")

    if df.duplicated(subset=["symbol", "date"]).any():
        raise ValueError("Hay periodos duplicados para una misma empresa.")


def validar_balance(df, periodos_esperados=None, tolerancia=1e-6):
    _validar_comun(df, COLUMNAS_BALANCE, periodos_esperados)

    if not df["total_assets"].notna().all():
        raise ValueError("Hay valores vacíos en total_assets.")

    # Tolerancia relativa para redondeos de la fuente; como mínimo 1 unidad
    # monetaria para que una deuda neta esperada de 0 no exija exactitud total.
    esperado = df["total_debt"] - df["cash_and_cash_equivalents"]
    diferencia = (df["net_debt"] - esperado).abs()
    margen = (tolerancia * esperado.abs()).clip(lower=1)

    no_cuadran = ~(diferencia <= margen)
    if no_cuadran.any():
        fechas = df.loc[no_cuadran, "date"].astype(str).tolist()
        raise ValueError(f"La deuda neta no coincide con el cálculo en: {fechas}")

    return True


def validar_cuenta_resultados(df, periodos_esperados=None):
    _validar_comun(df, COLUMNAS_RESULTADOS, periodos_esperados)

    if not df["revenue"].notna().all():
        raise ValueError("Hay valores vacíos en revenue.")

    if (df["gross_profit"] > df["revenue"]).any():
        raise ValueError("El beneficio bruto supera a los ingresos.")

    return True
