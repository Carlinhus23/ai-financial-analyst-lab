import pandas as pd
import pytest

from src.data.validator import (
    validar_balance,
    validar_cuenta_resultados,
    validar_flujos_caja,
)


def balance_valido(num_periodos=3):
    fechas = pd.date_range("2021-09-30", periods=num_periodos, freq="YE")
    return pd.DataFrame(
        {
            "symbol": ["AAPL"] * num_periodos,
            "date": fechas,
            "total_assets": [350_000_000_000] * num_periodos,
            "total_debt": [120_000_000_000] * num_periodos,
            "cash_and_cash_equivalents": [30_000_000_000] * num_periodos,
            "net_debt": [90_000_000_000] * num_periodos,
        }
    )


def test_balance_valido_pasa():
    assert validar_balance(balance_valido()) is True


def test_acepta_cualquier_numero_de_periodos_si_no_se_indica():
    assert validar_balance(balance_valido(num_periodos=2)) is True
    assert validar_balance(balance_valido(num_periodos=10)) is True


def test_falla_si_no_hay_los_periodos_esperados():
    with pytest.raises(ValueError, match="Se esperaban 5 periodos y hay 3"):
        validar_balance(balance_valido(num_periodos=3), periodos_esperados=5)


def test_falla_si_esta_vacio():
    with pytest.raises(ValueError, match="vacío"):
        validar_balance(balance_valido().iloc[0:0])


def test_falla_si_falta_una_columna():
    df = balance_valido().drop(columns=["net_debt"])

    with pytest.raises(ValueError, match="net_debt"):
        validar_balance(df)


def test_falla_si_hay_periodo_duplicado_en_la_misma_empresa():
    df = balance_valido()
    df.loc[1, "date"] = df.loc[0, "date"]

    with pytest.raises(ValueError, match="duplicados"):
        validar_balance(df)


def test_misma_fecha_en_empresas_distintas_es_valido():
    df = balance_valido(num_periodos=2)
    df["date"] = df.loc[0, "date"]
    df["symbol"] = ["AAPL", "MSFT"]

    assert validar_balance(df) is True


def test_falla_si_total_assets_tiene_nulos():
    df = balance_valido()
    df["total_assets"] = df["total_assets"].astype(float)
    df.loc[1, "total_assets"] = None

    with pytest.raises(ValueError, match="total_assets"):
        validar_balance(df)


def test_acepta_redondeo_pequeno_en_deuda_neta():
    df = balance_valido()
    df["net_debt"] = df["net_debt"] + 1_000  # 1.000 $ sobre 90.000 M$

    assert validar_balance(df) is True


def test_falla_si_deuda_neta_no_cuadra_e_indica_la_fecha():
    df = balance_valido()
    df.loc[2, "net_debt"] = 50_000_000_000

    with pytest.raises(ValueError, match="2023-12-31"):
        validar_balance(df)


def test_deuda_neta_esperada_cero_tolera_error_de_coma_flotante():
    df = balance_valido(num_periodos=1).astype({"net_debt": float})
    df["cash_and_cash_equivalents"] = df["total_debt"]
    df["net_debt"] = 1e-9

    assert validar_balance(df) is True


def test_falla_si_deuda_neta_es_nula():
    df = balance_valido().astype({"net_debt": float})
    df.loc[0, "net_debt"] = None

    with pytest.raises(ValueError, match="deuda neta"):
        validar_balance(df)


def resultados_validos():
    return pd.DataFrame(
        {
            "symbol": ["AAPL", "AAPL"],
            "date": pd.to_datetime(["2024-09-28", "2025-09-27"]),
            "revenue": [400, 420],
            "gross_profit": [180, 195],
            "operating_income": [120, 133],
            "net_income": [95, 112],
        }
    )


def test_cuenta_resultados_valida_pasa():
    assert validar_cuenta_resultados(resultados_validos()) is True


def test_cuenta_resultados_falla_si_faltan_columnas():
    df = resultados_validos().drop(columns=["net_income"])

    with pytest.raises(ValueError, match="net_income"):
        validar_cuenta_resultados(df)


def test_cuenta_resultados_falla_si_revenue_nulo():
    df = resultados_validos().astype({"revenue": float})
    df.loc[0, "revenue"] = None

    with pytest.raises(ValueError, match="revenue"):
        validar_cuenta_resultados(df)


def test_cuenta_resultados_falla_si_beneficio_bruto_supera_ingresos():
    df = resultados_validos()
    df.loc[1, "gross_profit"] = 500

    with pytest.raises(ValueError, match="beneficio bruto"):
        validar_cuenta_resultados(df)


def test_cuenta_resultados_comprueba_periodos_esperados():
    with pytest.raises(ValueError, match="Se esperaban 5 periodos y hay 2"):
        validar_cuenta_resultados(resultados_validos(), periodos_esperados=5)


def flujos_validos():
    return pd.DataFrame(
        {
            "symbol": ["AAPL", "AAPL"],
            "date": pd.to_datetime(["2024-09-28", "2025-09-27"]),
            "operating_cash_flow": [118, 111],
            "capital_expenditure": [-9, -13],
            "free_cash_flow": [109, 98],
        }
    )


def test_flujos_caja_validos_pasan():
    assert validar_flujos_caja(flujos_validos()) is True


def test_flujos_caja_falla_si_faltan_columnas():
    df = flujos_validos().drop(columns=["free_cash_flow"])

    with pytest.raises(ValueError, match="free_cash_flow"):
        validar_flujos_caja(df)


def test_flujos_caja_falla_si_flujo_operativo_nulo():
    df = flujos_validos().astype({"operating_cash_flow": float})
    df.loc[0, "operating_cash_flow"] = None

    with pytest.raises(ValueError, match="operating_cash_flow"):
        validar_flujos_caja(df)


def test_flujos_caja_falla_si_capex_positivo():
    df = flujos_validos()
    df["capital_expenditure"] = [9, 13]
    df["free_cash_flow"] = [127, 124]  # cuadraría, pero el signo está mal

    with pytest.raises(ValueError, match="capital_expenditure"):
        validar_flujos_caja(df)


def test_flujos_caja_falla_si_fcf_no_cuadra_e_indica_la_fecha():
    df = flujos_validos()
    df.loc[1, "free_cash_flow"] = 111  # FCF = OCF: como si ignorara el capex

    with pytest.raises(ValueError, match="2025-09-27"):
        validar_flujos_caja(df)
