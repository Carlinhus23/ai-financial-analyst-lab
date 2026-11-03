from src.financial.ratios import NOMBRES_RATIOS
from src.pipeline import actualizar_empresa, obtener_ratios

# Empresas del S&P 500 de sectores distintos, elegidas a mano. Sin bancos ni
# aseguradoras: su balance no tiene activo/pasivo corriente y varios ratios no
# tendrían sentido. Desde que los datos vienen de la SEC (03-11-2026) se puede
# añadir cualquier empresa que presente cuentas en EE. UU. (antes PG, CAT, LLY
# o las eléctricas eran de pago en FMP).
EMPRESAS = [
    "AAPL",  # Tecnología
    "MSFT",  # Tecnología
    "NVDA",  # Tecnología (semiconductores)
    "GOOGL",  # Comunicación
    "AMZN",  # Consumo discrecional
    "KO",  # Consumo básico
    "PEP",  # Consumo básico
    "WMT",  # Distribución
    "JNJ",  # Salud
    "XOM",  # Energía
    "GE",  # Industria
    "PFE",  # Salud (farmacéutica)
]
NUM_PERIODOS = 5

COLUMNAS_RATIOS = list(NOMBRES_RATIOS)


def main():
    fallidas = []
    for symbol in EMPRESAS:
        # Si una empresa falla (dato que no valida, error de FMP...), se
        # avisa y se sigue con las demás. Lo ya guardado de ella no se toca.
        try:
            actualizar_empresa(symbol, num_periodos=NUM_PERIODOS)
            print(f"{symbol}: datos actualizados.")
        except Exception as error:
            fallidas.append(symbol)
            print(f"{symbol}: NO actualizada -> {error}")

    ratios = obtener_ratios(EMPRESAS)

    for symbol, datos_empresa in ratios.groupby("symbol"):
        # Traspuesta: una fila por ratio y una columna por año, para que
        # quepa en la terminal.
        tabla = datos_empresa.set_index("fiscal_year")[COLUMNAS_RATIOS].round(3).T
        print(f"\n=== {symbol} ({datos_empresa['reported_currency'].iloc[0]}) ===")
        print(tabla.to_string())

    fuente = ratios["fuente"].iloc[0]
    extraccion = ratios["fecha_extraccion_utc"].max()
    print(f"\nFuente: {fuente} | extraído (UTC): {extraccion:%Y-%m-%d %H:%M}")
    if fallidas:
        print(f"Pipeline completado con errores en: {', '.join(fallidas)}")
    else:
        print("Pipeline completado correctamente.")


if __name__ == "__main__":
    main()
