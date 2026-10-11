import pandas as pd

CLAVES = ["symbol", "date"]


def convertir_a_snake_case(nombre):
    resultado = ""

    for caracter in nombre:
        if caracter.isupper():
            resultado += "_" + caracter.lower()
        else:
            resultado += caracter

    return resultado


def estado_a_dataframe(datos):
    # Sirve para cualquier estado de FMP (balance, cuenta de resultados...):
    # todos llegan como lista de diccionarios con camelCase y "date".
    df = pd.DataFrame(datos)

    df["date"] = pd.to_datetime(df["date"])

    df.columns = [convertir_a_snake_case(columna) for columna in df.columns]

    return df


def añadir_trazabilidad(df, fuente, fecha_extraccion=None):
    # Moneda y periodo ya vienen de la fuente (reported_currency, fiscal_year,
    # period). Aquí se añade de dónde y cuándo se sacó el dato.
    if fecha_extraccion is None:
        fecha_extraccion = pd.Timestamp.now(tz="UTC").tz_localize(None)

    df_resultado = df.copy()
    df_resultado["fuente"] = fuente
    df_resultado["fecha_extraccion_utc"] = fecha_extraccion
    return df_resultado


def unir_estados(balance, resultados):
    # Une balance y cuenta de resultados fila a fila por empresa y fecha.
    # Las columnas repetidas (moneda, cik, fuente...) se toman del balance.
    repetidas = [
        c for c in resultados.columns if c in balance.columns and c not in CLAVES
    ]

    return balance.merge(
        resultados.drop(columns=repetidas),
        on=CLAVES,
        how="inner",
        validate="one_to_one",
    )
