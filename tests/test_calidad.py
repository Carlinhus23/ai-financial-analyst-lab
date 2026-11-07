import pandas as pd

from src.financial.calidad import ENTRADAS_RATIOS, NOMBRES_PARTIDAS, ratios_sin_dato
from src.financial.ratios import (
    NOMBRES_RATIOS,
    calcular_crecimiento,
    calcular_ratios_balance,
    calcular_ratios_flujos_caja,
    calcular_ratios_rentabilidad,
)

NAN = float("nan")


def _ratios(**cambios):
    # Dos ejercicios de una empresa con todas las partidas; `cambios` cambia
    # columnas (listas de 2 valores). Se calculan los ratios como en pipeline.
    datos = {
        "symbol": ["XYZ", "XYZ"],
        "fiscal_year": ["2024", "2025"],
        "total_assets": [400.0, 420.0],
        "total_debt": [100.0, 100.0],
        "total_stockholders_equity": [200.0, 210.0],
        "total_current_assets": [150.0, 160.0],
        "total_current_liabilities": [100.0, 100.0],
        "inventory": [20.0, 25.0],
        "cash_and_cash_equivalents": [50.0, 55.0],
        "revenue": [500.0, 550.0],
        "gross_profit": [200.0, 220.0],
        "operating_income": [100.0, 110.0],
        "net_income": [80.0, 90.0],
        "operating_cash_flow": [120.0, 130.0],
        "capital_expenditure": [-20.0, -25.0],
    }
    datos.update(cambios)
    df = pd.DataFrame(datos)
    for calcular in [
        calcular_ratios_balance,
        calcular_ratios_rentabilidad,
        calcular_ratios_flujos_caja,
        calcular_crecimiento,
    ]:
        df = calcular(df)
    return df


def test_cada_ratio_dice_de_que_partidas_depende():
    assert sorted(ENTRADAS_RATIOS) == sorted(NOMBRES_RATIOS)
    for entradas in ENTRADAS_RATIOS.values():
        assert all(partida in NOMBRES_PARTIDAS for partida in entradas)


def test_con_todos_los_datos_no_hay_vacios():
    # El crecimiento del primer año falta siempre, pero no se cuenta.
    assert ratios_sin_dato(_ratios()) == []


def test_explica_la_partida_que_falta_en_la_sec():
    filas = ratios_sin_dato(_ratios(inventory=[NAN, NAN]))

    prueba_acida = [f for f in filas if f["ratio"] == "Prueba ácida"]
    assert prueba_acida == [
        {
            "symbol": "XYZ",
            "ratio": "Prueba ácida",
            "motivo": "Falta en la SEC: inventario",
            "años": "2024, 2025",
        }
    ]


def test_explica_cuando_lo_vacia_una_regla_y_no_un_dato():
    filas = ratios_sin_dato(_ratios(total_stockholders_equity=[200.0, -10.0]))

    roe = [f for f in filas if f["ratio"] == "ROE"]
    assert roe[0]["motivo"] == "Patrimonio neto 0 o negativo"
    assert roe[0]["años"] == "2025"


def test_crecimiento_del_beneficio_tras_un_año_de_perdidas():
    filas = ratios_sin_dato(_ratios(net_income=[-5.0, 90.0]))

    crecimiento = [f for f in filas if f["ratio"] == "Crecimiento del beneficio"]
    assert crecimiento[0]["años"] == "2025"  # 2024 (primer año) no cuenta
    assert "beneficio era 0 o negativo" in crecimiento[0]["motivo"]
