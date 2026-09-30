import duckdb


def guardar_balance_sheet(
    df,
    ruta_db="ai_financial_analyst.duckdb",
):
    conexion = duckdb.connect(ruta_db)

    conexion.execute("""
        CREATE OR REPLACE TABLE balance_sheet AS
        SELECT * FROM df
    """)
def obtener_balance_sheet(
    ruta_db="ai_financial_analyst.duckdb",
):
    conexion = duckdb.connect(ruta_db)

    resultado = conexion.execute("""
        SELECT
            date,
            symbol,
            total_assets,
            total_debt,
            net_debt
        FROM balance_sheet
        ORDER BY date
    """).df()

    conexion.close()

    return resultado