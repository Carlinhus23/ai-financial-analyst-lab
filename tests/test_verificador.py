from src.llm.verificador import cifras_no_encontradas

FICHA = "Deuda / activos: 2024: 35,5 % | 2025: 25,0 %\nLiquidez corriente: 2025: 1,50"


def test_si_todas_las_cifras_estan_en_la_ficha_no_avisa():
    texto = "En 2025 la deuda / activos baja del 35,5 % al 25,0 %."

    assert cifras_no_encontradas(texto, FICHA) == []


def test_detecta_una_cifra_inventada():
    texto = "La deuda baja al 25,0 %, unos 10,5 puntos menos."

    assert cifras_no_encontradas(texto, FICHA) == ["10,5"]


def test_la_misma_cifra_escrita_de_otra_forma_no_es_inventada():
    # "1,5" y "25" valen lo mismo que "1,50" y "25,0" de la ficha.
    texto = "La liquidez corriente es 1,5 y la deuda el 25 %."

    assert cifras_no_encontradas(texto, FICHA) == []


def test_cada_cifra_dudosa_sale_una_vez_y_en_orden():
    texto = "Sube a 40,1 %. Luego 7. Otra vez 40,1 %."

    assert cifras_no_encontradas(texto, FICHA) == ["40,1", "7"]
