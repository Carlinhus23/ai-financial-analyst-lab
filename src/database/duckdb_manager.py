import duckdb

RUTA_DB = "ai_financial_analyst.duckdb"

# El nombre de tabla se pega dentro del SQL; solo se aceptan estos para que
# nunca entre texto arbitrario en una consulta.
TABLAS_PERMITIDAS = {
    "balance_sheet",
    "income_statement",
    "cash_flow_statement",
    "company_profile",
}


def _comprobar_tabla(tabla):
    if tabla not in TABLAS_PERMITIDAS:
        raise ValueError(f"Tabla no permitida: {tabla}")


def guardar_estado(df, tabla, ruta_db=RUTA_DB):
    # Acumula: sustituye solo las filas de las mismas (symbol, date) que trae
    # df y conserva el resto (otras empresas u otros años).
    _comprobar_tabla(tabla)

    with duckdb.connect(ruta_db) as conexion:
        conexion.execute(
            f"CREATE TABLE IF NOT EXISTS {tabla} AS SELECT * FROM df LIMIT 0"
        )

        conexion.execute("BEGIN TRANSACTION")
        conexion.execute(f"""
            DELETE FROM {tabla}
            WHERE (symbol, date) IN (SELECT symbol, date FROM df)
        """)
        conexion.execute(f"INSERT INTO {tabla} BY NAME SELECT * FROM df")
        conexion.execute("COMMIT")


def obtener_estado(tabla, symbols=None, ruta_db=RUTA_DB):
    _comprobar_tabla(tabla)

    consulta = f"SELECT * FROM {tabla}"
    parametros = []

    if symbols is not None:
        consulta += " WHERE symbol IN (SELECT UNNEST(?))"
        parametros = [list(symbols)]

    consulta += " ORDER BY symbol, date"

    with duckdb.connect(ruta_db) as conexion:
        return conexion.execute(consulta, parametros).df()


# Une los tres estados por empresa y fecha y trae solo las columnas que usan
# los ratios. Cada columna dice de qué tabla sale: así "inventory" es siempre
# el saldo del balance (b) y no la variación del flujo de caja.
# INNER JOIN: solo quedan los años que existen en los tres estados.
CONSULTA_ANALISIS = """
    SELECT
        b.symbol,
        b.date,
        b.fiscal_year,
        b.reported_currency,
        b.fuente,
        b.fecha_extraccion_utc,
        -- Balance
        b.total_assets,
        b.total_debt,
        b.total_stockholders_equity,
        b.total_current_assets,
        b.total_current_liabilities,
        b.inventory,
        b.cash_and_cash_equivalents,
        -- Cuenta de resultados
        r.revenue,
        r.gross_profit,
        r.operating_income,
        r.net_income,
        -- Flujos de caja
        f.operating_cash_flow,
        f.capital_expenditure
    FROM balance_sheet AS b
    INNER JOIN income_statement AS r
        ON r.symbol = b.symbol AND r.date = b.date
    INNER JOIN cash_flow_statement AS f
        ON f.symbol = b.symbol AND f.date = b.date
"""


def obtener_datos_analisis(symbols=None, ruta_db=RUTA_DB):
    consulta = CONSULTA_ANALISIS
    parametros = []

    if symbols is not None:
        consulta += " WHERE b.symbol IN (SELECT UNNEST(?))"
        parametros = [list(symbols)]

    consulta += " ORDER BY b.symbol, b.date"

    with duckdb.connect(ruta_db) as conexion:
        df = conexion.execute(consulta, parametros).df()

    # Si una tabla tuviera una (symbol, date) repetida, el JOIN multiplicaría
    # filas sin avisar y los ratios saldrían duplicados.
    if df.duplicated(subset=["symbol", "date"]).any():
        raise ValueError("La unión de estados tiene periodos duplicados.")

    return df


def obtener_empresas(ruta_db=RUTA_DB):
    # Empresas con los tres estados guardados (las que se pueden analizar).
    consulta = f"""
        SELECT DISTINCT symbol
        FROM ({CONSULTA_ANALISIS})
        ORDER BY symbol
    """
    with duckdb.connect(ruta_db) as conexion:
        try:
            filas = conexion.execute(consulta).fetchall()
        except duckdb.CatalogException:
            # Aún no existe alguna de las tablas: no hay empresas que analizar.
            return []
    return [fila[0] for fila in filas]
