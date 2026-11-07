import math

import pandas as pd
import pytest

from src.financial.ratios import (
    calcular_calidad_beneficio,
    calcular_crecimiento,
    calcular_deuda_sobre_activos,
    calcular_deuda_sobre_patrimonio,
    calcular_liquidez_corriente,
    calcular_margen_fcf,
    calcular_margenes,
    calcular_per,
    calcular_prueba_acida,
    calcular_ratio_caja,
    calcular_ratios_balance,
    calcular_ratios_flujos_caja,
    calcular_ratios_rentabilidad,
    calcular_roa,
    calcular_roe,
)


def test_calcula_deuda_sobre_activos_con_valores_conocidos():
    datos = pd.DataFrame(
        {
            "total_assets": [100, 80, 200],
            "total_debt": [30, 20, 50],
        }
    )

    resultado = calcular_deuda_sobre_activos(datos)

    assert resultado["deuda_sobre_activos"].tolist() == pytest.approx(
        [0.30, 0.25, 0.25]
    )


def test_no_modifica_el_dataframe_original():
    datos = pd.DataFrame(
        {
            "total_assets": [100],
            "total_debt": [30],
        }
    )

    calcular_deuda_sobre_activos(datos)

    assert "deuda_sobre_activos" not in datos.columns


def test_activos_cero_da_nan_sin_afectar_otras_filas():
    datos = pd.DataFrame(
        {
            "total_assets": [100, 0],
            "total_debt": [30, 20],
        }
    )

    resultado = calcular_deuda_sobre_activos(datos)

    assert resultado["deuda_sobre_activos"].iloc[0] == pytest.approx(0.30)
    assert pd.isna(resultado["deuda_sobre_activos"].iloc[1])


def test_activos_o_deuda_nulos_dan_nan():
    datos = pd.DataFrame(
        {
            "total_assets": [None, 100],
            "total_debt": [30, None],
        }
    )

    resultado = calcular_deuda_sobre_activos(datos)

    assert resultado["deuda_sobre_activos"].isna().all()


def test_liquidez_corriente_con_valores_conocidos():
    datos = pd.DataFrame(
        {
            "total_current_assets": [150, 100],
            "total_current_liabilities": [100, 0],
        }
    )

    resultado = calcular_liquidez_corriente(datos)["liquidez_corriente"]

    assert resultado.iloc[0] == pytest.approx(1.5)
    assert pd.isna(resultado.iloc[1])


def test_prueba_acida_resta_el_inventario():
    datos = pd.DataFrame(
        {
            "total_current_assets": [150],
            "inventory": [30],
            "total_current_liabilities": [100],
        }
    )

    resultado = calcular_prueba_acida(datos)

    assert resultado["prueba_acida"].iloc[0] == pytest.approx(1.2)


def test_ratio_caja_con_valores_conocidos():
    datos = pd.DataFrame(
        {
            "cash_and_cash_equivalents": [25],
            "total_current_liabilities": [100],
        }
    )

    resultado = calcular_ratio_caja(datos)

    assert resultado["ratio_caja"].iloc[0] == pytest.approx(0.25)


def test_deuda_sobre_patrimonio_nan_si_patrimonio_cero_o_negativo():
    datos = pd.DataFrame(
        {
            "total_debt": [50, 50, 50],
            "total_stockholders_equity": [100, 0, -20],
        }
    )

    resultado = calcular_deuda_sobre_patrimonio(datos)["deuda_sobre_patrimonio"]

    assert resultado.iloc[0] == pytest.approx(0.5)
    assert resultado.iloc[1:].isna().all()


def test_ratios_balance_anade_todos_y_conserva_symbol_y_date():
    datos = pd.DataFrame(
        {
            "symbol": ["AAPL"],
            "date": pd.to_datetime(["2025-09-27"]),
            "total_assets": [200],
            "total_debt": [50],
            "total_stockholders_equity": [100],
            "total_current_assets": [150],
            "inventory": [30],
            "total_current_liabilities": [100],
            "cash_and_cash_equivalents": [25],
        }
    )

    resultado = calcular_ratios_balance(datos)

    fila = resultado.iloc[0]
    assert fila["symbol"] == "AAPL"
    assert fila["date"] == pd.Timestamp("2025-09-27")
    assert fila["deuda_sobre_activos"] == pytest.approx(0.25)
    assert fila["deuda_sobre_patrimonio"] == pytest.approx(0.5)
    assert fila["liquidez_corriente"] == pytest.approx(1.5)
    assert fila["prueba_acida"] == pytest.approx(1.2)
    assert fila["ratio_caja"] == pytest.approx(0.25)
    assert "deuda_sobre_activos" not in datos.columns


def test_margenes_con_valores_conocidos():
    datos = pd.DataFrame(
        {
            "revenue": [200, 0],
            "gross_profit": [80, 10],
            "operating_income": [50, 5],
            "net_income": [30, 2],
        }
    )

    resultado = calcular_margenes(datos)

    assert resultado["margen_bruto"].iloc[0] == pytest.approx(0.40)
    assert resultado["margen_operativo"].iloc[0] == pytest.approx(0.25)
    assert resultado["margen_neto"].iloc[0] == pytest.approx(0.15)
    # Sin ingresos, ningún margen es calculable.
    assert (
        resultado[["margen_bruto", "margen_operativo", "margen_neto"]]
        .iloc[1]
        .isna()
        .all()
    )


def test_roa_con_valores_conocidos():
    datos = pd.DataFrame({"net_income": [30], "total_assets": [300]})

    assert calcular_roa(datos)["roa"].iloc[0] == pytest.approx(0.10)


def test_roe_nan_si_patrimonio_cero_o_negativo():
    datos = pd.DataFrame(
        {
            "net_income": [30, 30, 30],
            "total_stockholders_equity": [150, 0, -10],
        }
    )

    resultado = calcular_roe(datos)["roe"]

    assert resultado.iloc[0] == pytest.approx(0.20)
    assert resultado.iloc[1:].isna().all()


def test_roe_admite_perdidas():
    datos = pd.DataFrame({"net_income": [-15], "total_stockholders_equity": [150]})

    assert calcular_roe(datos)["roe"].iloc[0] == pytest.approx(-0.10)


def test_ratios_rentabilidad_anade_todos():
    datos = pd.DataFrame(
        {
            "revenue": [200],
            "gross_profit": [80],
            "operating_income": [50],
            "net_income": [30],
            "total_assets": [300],
            "total_stockholders_equity": [150],
        }
    )

    resultado = calcular_ratios_rentabilidad(datos)

    for columna in ["margen_bruto", "margen_operativo", "margen_neto", "roa", "roe"]:
        assert columna in resultado.columns
    assert "roa" not in datos.columns


def test_margen_fcf_resta_el_capex_negativo():
    datos = pd.DataFrame(
        {
            "operating_cash_flow": [120, 50],
            "capital_expenditure": [-20, -10],
            "revenue": [400, 0],
        }
    )

    resultado = calcular_margen_fcf(datos)

    assert resultado["flujo_caja_libre"].tolist() == [100, 40]
    assert resultado["margen_fcf"].iloc[0] == pytest.approx(0.25)
    assert pd.isna(resultado["margen_fcf"].iloc[1])


def test_calidad_beneficio_nan_si_beneficio_cero_o_negativo():
    datos = pd.DataFrame(
        {
            "operating_cash_flow": [150, 150, 150],
            "net_income": [100, 0, -50],
        }
    )

    resultado = calcular_calidad_beneficio(datos)["calidad_beneficio"]

    assert resultado.iloc[0] == pytest.approx(1.5)
    assert resultado.iloc[1:].isna().all()


def test_ratios_flujos_caja_anade_todos():
    datos = pd.DataFrame(
        {
            "operating_cash_flow": [150],
            "capital_expenditure": [-30],
            "revenue": [600],
            "net_income": [100],
        }
    )

    resultado = calcular_ratios_flujos_caja(datos)

    for columna in ["flujo_caja_libre", "margen_fcf", "calidad_beneficio"]:
        assert columna in resultado.columns
    assert "margen_fcf" not in datos.columns


def test_per_con_valores_conocidos():
    assert calcular_per(2400, 120) == pytest.approx(20)


def test_per_nan_si_beneficio_cero_negativo_o_vacio():
    assert math.isnan(calcular_per(2400, 0))
    assert math.isnan(calcular_per(2400, -50))
    assert math.isnan(calcular_per(2400, float("nan")))


def test_crecimiento_compara_con_el_año_anterior_de_la_misma_empresa():
    datos = pd.DataFrame(
        {
            "symbol": ["AAPL", "AAPL", "KO", "KO"],
            "fiscal_year": ["2024", "2025", "2024", "2025"],
            "revenue": [100, 110, 50, 40],
            "net_income": [20, 30, 10, 5],
        }
    )

    resultado = calcular_crecimiento(datos)

    # El primer año de cada empresa no tiene anterior: KO no se compara con AAPL.
    assert math.isnan(resultado["crecimiento_ventas"][0])
    assert math.isnan(resultado["crecimiento_ventas"][2])
    assert resultado["crecimiento_ventas"][1] == pytest.approx(0.10)
    assert resultado["crecimiento_ventas"][3] == pytest.approx(-0.20)
    assert resultado["crecimiento_beneficio"][1] == pytest.approx(0.50)
    assert resultado["crecimiento_beneficio"][3] == pytest.approx(-0.50)


def test_crecimiento_nan_si_falta_un_año_o_venia_de_perdidas():
    datos = pd.DataFrame(
        {
            "symbol": ["GE", "GE", "GE"],
            "fiscal_year": ["2021", "2023", "2024"],
            "revenue": [100, 120, 130],
            "net_income": [10, -5, 8],
        }
    )

    resultado = calcular_crecimiento(datos)

    # 2023 no se compara con 2021 (falta 2022): sería crecimiento de dos años.
    assert math.isnan(resultado["crecimiento_ventas"][1])
    # 2024 sí tiene ventas de 2023, pero en 2023 hubo pérdidas: % sin sentido.
    assert resultado["crecimiento_ventas"][2] == pytest.approx(130 / 120 - 1)
    assert math.isnan(resultado["crecimiento_beneficio"][2])
