import duckdb

RUTA_DB = "ai_financial_analyst.duckdb"

# El nombre de tabla se pega dentro del SQL; solo se aceptan estos para que
# nunca entre texto arbitrario en una consulta.
TABLAS_PERMITIDAS = {"balance_sheet", "income_statement"}


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
