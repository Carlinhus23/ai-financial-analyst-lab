# Orquesta el motor: une las piezas de src/ en operaciones de alto nivel.
# main.py y Django solo llaman a estas funciones.

from src.data.sec_client import (
    get_balance_sheet,
    get_cash_flow_statement,
    get_income_statement,
)
from src.data.transformer import añadir_trazabilidad, estado_a_dataframe
from src.data.validator import (
    validar_balance,
    validar_cuenta_resultados,
    validar_flujos_caja,
    validar_perfil,
)
from src.data.yahoo_client import get_profile
from src.database.duckdb_manager import (
    RUTA_DB,
    guardar_estado,
    obtener_datos_analisis,
    obtener_empresas,
    obtener_estado,
)
from src.financial.ratios import (
    NOMBRES_RATIOS,
    calcular_crecimiento,
    calcular_per,
    calcular_ratios_balance,
    calcular_ratios_flujos_caja,
    calcular_ratios_rentabilidad,
)
from src.formato import formatear
from src.llm.explicador import explicar
from src.llm.verificador import cifras_no_encontradas

# Cada dato guarda de dónde sale: estados de la SEC, cotización de Yahoo.
FUENTE = "SEC EDGAR (10-K)"
FUENTE_COTIZACION = "Yahoo Finance"


def actualizar_empresa(symbol, num_periodos=5, ruta_db=RUTA_DB):
    # Descarga, limpia, valida y guarda los tres estados y el perfil.
    # Si algo no valida, se lanza el error antes de guardar nada.
    balance = estado_a_dataframe(get_balance_sheet(symbol, limit=num_periodos))
    balance = añadir_trazabilidad(balance, fuente=FUENTE)
    validar_balance(balance, periodos_esperados=num_periodos)

    resultados = estado_a_dataframe(get_income_statement(symbol, limit=num_periodos))
    resultados = añadir_trazabilidad(resultados, fuente=FUENTE)
    validar_cuenta_resultados(resultados, periodos_esperados=num_periodos)

    flujos = estado_a_dataframe(get_cash_flow_statement(symbol, limit=num_periodos))
    flujos = añadir_trazabilidad(flujos, fuente=FUENTE)
    validar_flujos_caja(flujos, periodos_esperados=num_periodos)

    perfil = estado_a_dataframe(get_profile(symbol))
    perfil = añadir_trazabilidad(perfil, fuente=FUENTE_COTIZACION)
    # El perfil no trae fecha: se usa el día de descarga (una foto por día).
    perfil["date"] = perfil["fecha_extraccion_utc"].dt.normalize()
    validar_perfil(perfil)

    guardar_estado(balance, "balance_sheet", ruta_db)
    guardar_estado(resultados, "income_statement", ruta_db)
    guardar_estado(flujos, "cash_flow_statement", ruta_db)
    guardar_estado(perfil, "company_profile", ruta_db)


def obtener_ratios(symbols=None, ruta_db=RUTA_DB):
    # Lee lo guardado y calcula todos los ratios. No llama a la API.
    # La unión de los tres estados la hace SQL (ver obtener_datos_analisis);
    # las fórmulas se quedan en Python.
    df = obtener_datos_analisis(symbols, ruta_db)
    df = calcular_ratios_balance(df)
    df = calcular_ratios_rentabilidad(df)
    df = calcular_ratios_flujos_caja(df)
    df = calcular_crecimiento(df)
    return df


def obtener_perfil(symbol, ruta_db=RUTA_DB):
    # Último perfil guardado de la empresa más su PER. No llama a la API.
    # Devuelve un diccionario, o None si no hay perfil guardado.
    perfiles = obtener_estado("company_profile", [symbol], ruta_db)
    if perfiles.empty:
        return None

    perfil = perfiles.iloc[-1].to_dict()  # viene ordenado por fecha: el último
    datos = obtener_datos_analisis([symbol], ruta_db)
    perfil["per"] = calcular_per(perfil["market_cap"], datos["net_income"].iloc[-1])
    return perfil


def obtener_comparacion(ruta_db=RUTA_DB):
    # Último ejercicio de cada empresa, con su sector y su PER, para
    # compararlas. Devuelve una lista de diccionarios ordenada por sector.
    # Lee la base solo dos veces, sea cual sea el número de empresas.
    ultimos = obtener_ratios(None, ruta_db).groupby("symbol").tail(1)
    perfiles = obtener_estado("company_profile", ruta_db=ruta_db)
    ultimo_perfil = {p["symbol"]: p for p in perfiles.to_dict("records")}

    filas = []
    for fila in ultimos.to_dict("records"):
        perfil = ultimo_perfil.get(fila["symbol"], {})
        # "or": si Yahoo no dio el sector (None), "—"; así se puede ordenar.
        fila["sector"] = perfil.get("sector") or "—"
        # El mismo PER que obtener_perfil: el beneficio ya está en la fila.
        capitalizacion = perfil.get("market_cap", float("nan"))
        fila["per"] = calcular_per(capitalizacion, fila["net_income"])
        filas.append(fila)

    return sorted(filas, key=lambda fila: fila["sector"])


def ficha_empresa(symbol, ruta_db=RUTA_DB):
    # Texto con todas las cifras de una empresa, escritas igual que en la web.
    # Es lo único que recibe la IA: no puede ver ni inventar otras cifras.
    ratios = obtener_ratios([symbol], ruta_db)
    perfil = obtener_perfil(symbol, ruta_db) or {}

    nombre = perfil.get("company_name") or symbol
    sector = perfil.get("sector") or "—"
    per = formatear("per", perfil.get("per", float("nan")))
    lineas = [f"Empresa: {symbol} ({nombre}). Sector: {sector}. PER: {per}."]

    años = ratios["fiscal_year"].tolist()
    for columna, nombre_ratio in NOMBRES_RATIOS.items():
        valores = [
            f"{año}: {formatear(columna, valor)}"
            for año, valor in zip(años, ratios[columna], strict=True)
        ]
        lineas.append(f"{nombre_ratio}: " + " | ".join(valores))
    return "\n".join(lineas)


def explicar_empresa(symbol, ruta_db=RUTA_DB):
    # La IA explica la ficha de la empresa. Llama a Gemini: tarda unos segundos.
    # Devuelve (explicación, modelo que la ha escrito, cifras que la IA ha
    # escrito y no están en la ficha; vacía si todo cuadra).
    ficha = ficha_empresa(symbol, ruta_db)
    texto, modelo = explicar(ficha)
    return texto, modelo, cifras_no_encontradas(texto, ficha)


def listar_empresas(ruta_db=RUTA_DB):
    # Empresas que ya tienen datos guardados. No llama a la API.
    return obtener_empresas(ruta_db)
