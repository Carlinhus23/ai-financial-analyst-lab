from src.data.fmp_client import get_balance_sheet
from src.data.transformer import balance_sheet_a_dataframe
from src.data.validator import validar_balance
from src.database.duckdb_manager import (
    guardar_balance_sheet,
    obtener_balance_sheet,
)


symbol = "AAPL"

balance_sheets = get_balance_sheet(symbol, limit=5)

df = balance_sheet_a_dataframe(balance_sheets)

validar_balance(df)

guardar_balance_sheet(df)

df_guardado = obtener_balance_sheet()

print(df_guardado)

print("Pipeline completado correctamente.")