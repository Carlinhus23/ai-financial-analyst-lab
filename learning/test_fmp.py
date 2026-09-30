from src.data.fmp_client import get_balance_sheet
from src.data.transformer import balance_sheet_a_dataframe
from src.data.validator import validar_balance
from src.database.duckdb_manager import (
    guardar_balance_sheet,
    obtener_balance_sheet,
)


datos = get_balance_sheet("AAPL")

df = balance_sheet_a_dataframe(datos)

validar_balance(df)

guardar_balance_sheet(df)

print("Balance guardado correctamente en DuckDB.")

resultado = obtener_balance_sheet()

print(resultado.to_string(index=False))