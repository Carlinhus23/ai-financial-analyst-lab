COLUMNAS_BALANCE = [
    "symbol",
    "date",
    "total_assets",
    "total_debt",
    "cash_and_cash_equivalents",
    "total_liabilities_and_total_equity",
]

COLUMNAS_RESULTADOS = [
    "symbol",
    "date",
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
]

COLUMNAS_FLUJOS_CAJA = [
    "symbol",
    "date",
    "operating_cash_flow",
    "capital_expenditure",
]

COLUMNAS_PERFIL = [
    "symbol",
    "date",
    "company_name",
    "sector",
    "industry",
    "price",
    "change_percentage",
    "market_cap",
    "currency",
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


def _comprobar_cuadre(df, informado, esperado, nombre, tolerancia):
    # Comprueba que una cifra que da la fuente coincide con otra que debe ser
    # igual (por una identidad contable).
    # Tolerancia relativa para redondeos de la fuente; como mínimo 1 unidad
    # monetaria para que un valor esperado de 0 no exija exactitud total.
    diferencia = (informado - esperado).abs()
    margen = (tolerancia * esperado.abs()).clip(lower=1)

    no_cuadran = ~(diferencia <= margen)
    if no_cuadran.any():
        fechas = df.loc[no_cuadran, "date"].astype(str).tolist()
        raise ValueError(f"{nombre} no coincide con el cálculo en: {fechas}")


def validar_balance(df, periodos_esperados=None, tolerancia=1e-6):
    _validar_comun(df, COLUMNAS_BALANCE, periodos_esperados)

    if not df["total_assets"].notna().all():
        raise ValueError("Hay valores vacíos en total_assets.")

    # Identidad contable: activo = pasivo + patrimonio. Detecta cifras de
    # años o periodos mezclados al leer la fuente.
    _comprobar_cuadre(
        df,
        informado=df["total_assets"],
        esperado=df["total_liabilities_and_total_equity"],
        nombre="El balance (activo = pasivo + patrimonio)",
        tolerancia=tolerancia,
    )

    return True


def validar_cuenta_resultados(df, periodos_esperados=None):
    _validar_comun(df, COLUMNAS_RESULTADOS, periodos_esperados)

    if not df["revenue"].notna().all():
        raise ValueError("Hay valores vacíos en revenue.")

    if (df["gross_profit"] > df["revenue"]).any():
        raise ValueError("El beneficio bruto supera a los ingresos.")

    return True


def validar_flujos_caja(df, periodos_esperados=None):
    _validar_comun(df, COLUMNAS_FLUJOS_CAJA, periodos_esperados)

    if not df["operating_cash_flow"].notna().all():
        raise ValueError("Hay valores vacíos en operating_cash_flow.")

    # El capex llega en negativo (salida de caja) y nuestro FCF lo suma.
    # Si algún día llegara en positivo, el FCF saldría inflado sin avisar.
    if (df["capital_expenditure"] > 0).any():
        raise ValueError("capital_expenditure positivo: se esperaba en negativo.")

    return True


def validar_perfil(df):
    # Una sola fila: la foto del día de la empresa.
    _validar_comun(df, COLUMNAS_PERFIL, periodos_esperados=1)

    # La capitalización se usa para el PER: tiene que existir y ser positiva.
    if not (df["market_cap"] > 0).all():
        raise ValueError("market_cap vacío o no positivo.")

    return True
