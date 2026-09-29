import os
import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("API_KEY")

url = "https://financialmodelingprep.com/stable/balance-sheet-statement"

params = {
    "symbol": "AAPL",
    "period": "annual",
    "limit": 5,
    "apikey": api_key,
}

response = requests.get(url, params=params, timeout=30)

print(response.status_code)

datos = response.json()
for balance in datos:
    print(balance["date"], balance["totalAssets"])

print(type(datos))
print(len(datos))
print(datos[0])

print("TIPO DE DATOS:", type(datos))
print("NÚMERO DE BALANCES:", len(datos))

primer_balance = datos[0]

print("TIPO DEL PRIMER BALANCE:", type(primer_balance))
print("FECHA:", primer_balance["date"])
print("EMPRESA:", primer_balance["symbol"])
print("ACTIVOS:", primer_balance["totalAssets"])

for balance in datos:
    print(
        f"Balance {balance['fiscalYear']}: "
        f"Activos: {balance['totalAssets']} | "
        f"Deudas: {balance['totalDebt']}"
    )

def analizar_empresa(nombre):
    print(f"Analizando {nombre}")


analizar_empresa("Apple")
analizar_empresa("Microsoft")
analizar_empresa("Amazon")

def calcular_deuda_neta(balance):
    deuda_neta = balance["totalDebt"] - balance["cashAndCashEquivalents"]
    return deuda_neta

print(calcular_deuda_neta(datos[0]))

for balance in datos:
    deuda_neta = calcular_deuda_neta(balance)
    print(
        f"Balance {balance['fiscalYear']}: "
        f"Deuda neta: {deuda_neta}"
    )

df = pd.DataFrame(datos)

df["net_debt_calculated"] = (
    df["totalDebt"] - df["cashAndCashEquivalents"]
)
print(df[["date", "totalDebt", "cashAndCashEquivalents", "net_debt_calculated", "netDebt"]].to_string(index=False))

df["net_debt_difference"] = (
    df["netDebt"] - df["net_debt_calculated"]
)

print(
    df[
        [
            "date",
            "netDebt",
            "net_debt_calculated",
            "net_debt_difference"
        ]
    ].to_string(index=False)
)

print((df["netDebt"] == df["net_debt_calculated"]).all())

print(len(df) == 5)

print(df["date"].is_unique)

print(df["totalAssets"].notna().all())

def validar_balance(df):
    print("Número de filas correcto:", len(df) == 5)
    print("Fechas únicas:", df["date"].is_unique)
    print("Total Assets sin valores vacíos:", df["totalAssets"].notna().all())

def validar_balance(df):
    if len(df) == 5:
        print("Número de filas: OK")
    else:
        print("ERROR: número de filas incorrecto")
    if df["date"].is_unique:
        print("Fechas únicas: OK")
    else:
        print("ERROR: hay fechas duplicadas")
    if df["totalAssets"].notna().all():
        print("Total Assets: OK")
    else:
        print("ERROR: hay valores vacíos en Total Assets")

validar_balance(df)


def validar_balance(df):

    if len(df) != 5:
        raise ValueError("El balance no contiene exactamente 5 años.")

    if not df["date"].is_unique:
        raise ValueError("Hay fechas duplicadas.")

    if not df["totalAssets"].notna().all():
        raise ValueError("Hay valores vacíos en Total Assets.")

    deuda_correcta = (
        df["netDebt"]
        == df["totalDebt"] - df["cashAndCashEquivalents"]
    ).all()

    if not deuda_correcta:
        raise ValueError("La deuda neta no coincide con el cálculo.")

    return True


try:
    resultado = validar_balance(df)
    print("Balance validado:", resultado)

except ValueError as error:
    print("Se ha producido un error:", error)