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


cantidad = conexion.execute("""
    SELECT COUNT(*)
    FROM balance_sheet
""").fetchone()

print(cantidad)


maxima_debt = conexion.execute("""
    SELECT MAX(total_debt)
    FROM balance_sheet
    WHERE symbol = 'AAPL'
""").fetchone()

print("Maxima deuda de Apple",maxima_debt)

menor_debt = conexion.execute("""
    SELECT date, total_assets
    FROM balance_sheet
    WHERE symbol = 'AAPL'
    ORDER BY total_assets ASC
    LIMIT 1
""").fetchone()

print("MENOR TOTAL ASSETS:", menor_debt)

conexion.close()