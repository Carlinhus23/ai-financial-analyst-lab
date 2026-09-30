import os

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("API_KEY")

if not api_key:
    raise RuntimeError("No se encontró API_KEY en el archivo .env.")

url = "https://financialmodelingprep.com/stable/balance-sheet-statement"
params = {
    "symbol": "AAPL",
    "period": "annual",
    "limit": 5,
    "apikey": api_key,
}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()


balance_sheets = response.json()

if not isinstance(balance_sheets, list):
    raise ValueError("FMP no devolvió una lista de balances.")

df = pd.DataFrame(balance_sheets)
df["date"] = pd.to_datetime(df["date"])
df_chronological = df.sort_values("date")
print("¿Cinco balances?", len(df_chronological) == 5)
print("¿Fechas únicas?", df_chronological["date"].is_unique)
print("¿Todos anuales?", (df_chronological["period"] == "FY").all())

print(df.shape)
print(
    df_chronological[["date", "symbol", "cashAndCashEquivalents", "totalAssets", "totalDebt"]].to_string(
        formatters={
            "cashAndCashEquivalents": "{:,.0f}".format,
            "totalAssets": "{:,.0f}".format,
            "totalDebt": "{:,.0f}".format,
        },
        index=False,
    )
)

print(
    df_chronological[
        ["date", "cashAndCashEquivalents", "totalAssets", "totalDebt"]
    ].dtypes
)

print(f"Balances anuales recibidos: {len(balance_sheets)}")

for balance_sheet in balance_sheets:
    print(
        f"Balance {balance_sheet['period']}: "
        f"fecha de cierre {balance_sheet['date']}"
    )
