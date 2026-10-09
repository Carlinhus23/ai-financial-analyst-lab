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

menor_assets = conexion.execute("""
    SELECT date, total_assets
    FROM balance_sheet
    WHERE symbol = 'AAPL'
    ORDER BY total_assets ASC
    LIMIT 1
""").fetchone()

print("MENOR TOTAL ASSETS:", menor_assets)

resultado_grupos = conexion.execute("""
SELECT
    symbol,
    COUNT(*)
FROM balance_sheet
GROUP BY symbol
""").df()

print("Numero total de registros que tengo por empresa:", resultado_grupos)

promedio_assets = conexion.execute("""
    SELECT  
        AVG(total_assets)
    FROM balance_sheet
    WHERE symbol = 'AAPL'
""").fetchone()

print("Promedio de activos totales:", promedio_assets)

promedio_por_empresa = conexion.execute("""
    SELECT  
        symbol,
        AVG(total_assets) AS promedio_activos
    FROM balance_sheet
    GROUP BY symbol
""").df()

print("Promedio de activos por empresa:", promedio_por_empresa)

suma_assets = conexion.execute("""
    SELECT
        SUM(total_assets)
    FROM balance_sheet
    WHERE symbol = 'AAPL'
""").fetchone()

print("Suma de activos totales:", suma_assets)


empresas_grandes = conexion.execute("""
    SELECT
        symbol,
        AVG(total_assets) AS avg_assets
    FROM balance_sheet
    GROUP BY symbol
    HAVING AVG(total_assets) > 300000
""").df()

print(empresas_grandes)

empresas_grandes_con_4_registros = conexion.execute("""
    SELECT
        symbol,
        COUNT(*) AS num_registros,
        AVG(total_assets) AS avg_assets
    FROM balance_sheet
    GROUP BY symbol
    HAVING COUNT(*) >= 4 AND AVG(total_assets) > 300000
""").df()

print(empresas_grandes_con_4_registros)

categorias = conexion.execute("""
    SELECT
        symbol,
        date,
        total_assets,
        CASE
             WHEN total_assets > 360000000000 THEN 'Muy Grande'
        ELSE 'Grande'
        END AS categoria
    FROM balance_sheet
""").df()

print(categorias)

tres_categorias = conexion.execute("""
    SELECT
        symbol,
        date,
        total_assets,
        CASE
             WHEN total_assets >= 360000000000 THEN 'Muy Grande'
             WHEN total_assets > 355000000000 THEN 'Grande'
        ELSE 'Mediana'
        END AS categoria
    FROM balance_sheet
""").df()

print(tres_categorias)

debt_to_assets = conexion.execute("""
    SELECT
        symbol,
        date,
        total_debt,
        total_assets,
        total_debt / total_assets AS debt_to_assets_ratio
    FROM balance_sheet
""").df()

print(debt_to_assets)

debt_levels = conexion.execute("""
    SELECT
        symbol,
        date,
        total_debt,
        total_assets,
        ROUND(total_debt / total_assets, 2) AS debt_to_assets_ratio,
        CASE
             WHEN debt_to_assets_ratio > 0.5 THEN 'Alto'
             WHEN debt_to_assets_ratio >= 0.3 THEN 'Medio'
        ELSE 'Bajo'
        END AS nivel_deuda
    FROM balance_sheet
    ORDER BY debt_to_assets_ratio DESC
""").df()

print(debt_levels)

conexion.close()    