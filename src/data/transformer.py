import pandas as pd


def convertir_a_snake_case(nombre):

    resultado = ""

    for caracter in nombre:

        if caracter.isupper():
            resultado += "_" + caracter.lower()
        else:
            resultado += caracter

    return resultado


def balance_sheet_a_dataframe(datos):

    df = pd.DataFrame(datos)

    df["date"] = pd.to_datetime(df["date"])

    df.columns = [
        convertir_a_snake_case(columna)
        for columna in df.columns
    ]

    return df