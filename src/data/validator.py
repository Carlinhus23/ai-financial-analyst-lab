def validar_balance(df):

    if len(df) != 5:
        raise ValueError(
            "El balance no contiene exactamente 5 años."
        )

    if not df["date"].is_unique:
        raise ValueError(
            "Hay fechas duplicadas."
        )

    if not df["total_assets"].notna().all():
        raise ValueError(
            "Hay valores vacíos en total_assets."
        )

    if not (
        df["net_debt"]
        == df["total_debt"] - df["cash_and_cash_equivalents"]
    ).all():
        raise ValueError(
            "La deuda neta no coincide con el cálculo."
        )

    return True