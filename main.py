from src.pipeline import actualizar_empresa, obtener_ratios

EMPRESAS = ["AAPL", "MSFT", "KO"]
NUM_PERIODOS = 5

COLUMNAS_RATIOS = [
    "deuda_sobre_activos",
    "deuda_sobre_patrimonio",
    "liquidez_corriente",
    "prueba_acida",
    "ratio_caja",
    "margen_bruto",
    "margen_operativo",
    "margen_neto",
    "roa",
    "roe",
    "margen_fcf",
    "calidad_beneficio",
]


def main():
    for symbol in EMPRESAS:
        actualizar_empresa(symbol, num_periodos=NUM_PERIODOS)
        print(f"{symbol}: datos actualizados.")

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
    print("Pipeline completado correctamente.")


if __name__ == "__main__":
    main()
