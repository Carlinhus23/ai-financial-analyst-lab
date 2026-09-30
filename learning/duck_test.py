import duckdb

conexion = duckdb.connect("ai_financial_analyst.duckdb")

print("Base de datos conectada correctamente")

conexion.close()