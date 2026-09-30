import os

import duckdb
import pandas as pd
import requests
from dotenv import load_dotenv


# -------------------------
# 1. Cargar API key
# -------------------------

load_dotenv()

api_key = os.getenv("API_KEY")

if not api_key:
    raise RuntimeError("No se encontró API_KEY en el archivo .env.")


# -------------------------
# 2. Obtener datos de Apple
# -------------------------

url = "https://financialmodelingprep.com/stable/balance-sheet-statement"

params = {
    "symbol": "AAPL",
    "period": "annual",
    "limit": 5,
    "apikey": api_key,
}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()

datos = response.json()


# -------------------------
# 3. Convertir a DataFrame
# -------------------------

df = pd.DataFrame(datos)

df["date"] = pd.to_datetime(df["date"])

print("Datos descargados:", len(df))
print(df[["date", "symbol", "totalAssets"]])

def convertir_a_snake_case(nombre):

    resultado = ""

    for caracter in nombre:

        if caracter.isupper():
            resultado += "_" + caracter.lower()
        else:
            resultado += caracter

    return resultado

df.columns = [
    convertir_a_snake_case(columna)
    for columna in df.columns
]

print(df.columns.tolist())
# -------------------------
# 4. Conectar con DuckDB
# -------------------------

conexion = duckdb.connect("ai_financial_analyst.duckdb")

print("Conectado a DuckDB")


# -------------------------
# 5. Guardar DataFrame
# -------------------------

conexion.execute("""
    CREATE OR REPLACE TABLE balance_sheet AS
    SELECT * FROM df
""")

print("Balance Sheet guardado en DuckDB")


# -------------------------
# 6. Consultar la tabla
# -------------------------

resultado = conexion.execute("""
    SELECT
        date,
        symbol,
        total_assets,
        total_debt
    FROM balance_sheet
    ORDER BY date
""").df()

print(resultado.to_string(index=False))


# -------------------------
# 7. Cerrar conexión
# -------------------------

conexion.close()

print("Conexión cerrada")