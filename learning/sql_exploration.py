import duckdb


conexion = duckdb.connect("ai_financial_analyst.duckdb")

resultado = conexion.execute("""
    SELECT
        date,
        total_assets
    FROM balance_sheet
    ORDER BY date
""").df()

print(resultado)

resultado_completo = conexion.execute("""
    SELECT *
    FROM balance_sheet
    ORDER BY date
""").df()

print(resultado_completo)

conexion.close()