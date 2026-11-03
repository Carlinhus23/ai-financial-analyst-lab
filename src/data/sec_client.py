# Estados financieros oficiales desde SEC EDGAR (cuentas anuales 10-K), gratis
# y sin clave. Devuelve los datos con los mismos nombres que usaba FMP, para
# que el resto del motor no cambie (este archivo hace de "traductor").

import functools
import math
import os
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

URL_TICKERS = "https://www.sec.gov/files/company_tickers.json"
URL_HECHOS = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

# Cada partida y las etiquetas XBRL (us-gaap) que la representan, por orden de
# preferencia: cada año vale la primera que tenga dato. Hacen falta varias
# porque cada empresa etiqueta a su manera (ver docs/decisiones.md).
ETIQUETAS = {
    # Balance
    "totalAssets": ["Assets"],
    "totalLiabilitiesAndTotalEquity": ["LiabilitiesAndStockholdersEquity"],
    "totalStockholdersEquity": [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    ],
    "totalCurrentAssets": ["AssetsCurrent"],
    "totalCurrentLiabilities": ["LiabilitiesCurrent"],
    "inventory": ["InventoryNet", "EnergyRelatedInventory"],
    "cashAndCashEquivalents": [
        "CashAndCashEquivalentsAtCarryingValue",
        "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
    ],
    # Piezas de la deuda financiera (se suman en get_balance_sheet)
    "deudaNoCorriente": [
        "LongTermDebtNoncurrent",
        "LongTermDebtAndCapitalLeaseObligations",
    ],
    "deudaCorriente": ["DebtCurrent"],
    "deudaLargoQueVence": [
        "LongTermDebtCurrent",
        "LongTermDebtAndCapitalLeaseObligationsCurrent",
    ],
    "pagares": ["CommercialPaper"],
    "prestamosCorto": ["ShortTermBorrowings"],
    "otrosPrestamosCorto": ["OtherShortTermBorrowings"],
    # Cuenta de resultados
    "revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
    ],
    "grossProfit": ["GrossProfit"],
    "costeVentas": ["CostOfRevenue", "CostOfGoodsAndServicesSold"],
    "operatingIncome": ["OperatingIncomeLoss"],
    "netIncome": ["NetIncomeLoss"],
    # Flujos de caja
    "operatingCashFlow": ["NetCashProvidedByUsedInOperatingActivities"],
    "pagosCapex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
    ],
}

VACIO = float("nan")

# Excepciones a la tabla ticker -> CIK de la SEC. En 2026 ExxonMobil creó una
# holding nueva (CIK 2115436) que ahora tiene el ticker XOM pero aún no ha
# presentado ninguna cuenta anual: sus 10-K siguen en la sociedad anterior.
# Se puede quitar cuando la holding presente su primer 10-K.
CIKS_MANUALES = {"XOM": "0000034088"}


def _get_json(url):
    # La SEC exige identificarse con nombre y email en el User-Agent.
    agente = os.getenv("SEC_USER_AGENT")
    if not agente:
        raise RuntimeError(
            "Falta SEC_USER_AGENT en .env (tu nombre y email: lo exige la SEC)."
        )

    try:
        response = requests.get(url, headers={"User-Agent": agente}, timeout=30)
    except requests.RequestException as error:
        raise RuntimeError(
            f"No se pudo conectar con la SEC ({type(error).__name__})."
        ) from None

    if not response.ok:
        raise RuntimeError(f"La SEC respondió {response.status_code} al pedir {url}.")

    return response.json()


@functools.cache
def _ciks():
    # Tabla ticker -> CIK (número de empresa en la SEC, con 10 cifras).
    # functools.cache: se descarga una sola vez por ejecución.
    empresas = _get_json(URL_TICKERS).values()
    return {e["ticker"]: str(e["cik_str"]).zfill(10) for e in empresas}


@functools.cache
def _hechos(symbol):
    # Todas las cifras XBRL de la empresa. Una descarga sirve para los tres
    # estados, porque los tres get_... la piden y queda guardada.
    cik = CIKS_MANUALES.get(symbol) or _ciks().get(symbol)
    if cik is None:
        raise ValueError(f"La SEC no tiene la empresa {symbol}.")
    return _get_json(URL_HECHOS.format(cik=cik))["facts"]["us-gaap"]


def _anuales(hechos, etiqueta):
    # {fecha de cierre: valor} de una etiqueta, solo de cuentas anuales (10-K).
    # Si un cierre aparece en varias cuentas, vale la presentada más tarde.
    # Los importes de un periodo (ventas, flujos) deben cubrir un año entero.
    valores = {}
    filas = hechos.get(etiqueta, {}).get("units", {}).get("USD", [])
    for fila in sorted(filas, key=lambda f: f["filed"]):
        if not fila["form"].startswith("10-K"):
            continue
        if "start" in fila:
            dias = date.fromisoformat(fila["end"]) - date.fromisoformat(fila["start"])
            if not 350 <= dias.days <= 380:
                continue
        # float: así DuckDB guarda la columna como decimal y, al leerla, los
        # huecos vuelven como NaN (con enteros volverían como <NA> y fallaría
        # math.isnan en la web).
        valores[fila["end"]] = float(fila["val"])
    return valores


def _serie(hechos, etiquetas):
    # Para cada cierre, el valor de la primera etiqueta que lo tenga.
    serie = {}
    for etiqueta in etiquetas:
        for cierre, valor in _anuales(hechos, etiqueta).items():
            serie.setdefault(cierre, valor)
    return serie


def _ejercicio(cierre):
    # Año del ejercicio. Algunas empresas cierran en el domingo más cercano a
    # fin de año: el ejercicio 2022 de J&J cerró el 1-1-2023. Restar 7 días
    # deja esos cierres en el año que les corresponde.
    return str((date.fromisoformat(cierre) - timedelta(days=7)).year)


def _años(symbol, limit):
    # Los últimos `limit` cierres anuales, cada uno con todas las partidas.
    hechos = _hechos(symbol)
    series = {
        campo: _serie(hechos, etiquetas) for campo, etiquetas in ETIQUETAS.items()
    }
    cierres = sorted(series["totalAssets"], reverse=True)[:limit]

    años = []
    for cierre in cierres:
        año = {campo: serie.get(cierre, VACIO) for campo, serie in series.items()}
        año["symbol"] = symbol
        año["date"] = cierre
        año["fiscalYear"] = _ejercicio(cierre)
        año["reportedCurrency"] = "USD"
        años.append(año)
    return años


def _sumar(*valores):
    # Suma ignorando los vacíos; si todos están vacíos, vacío.
    con_dato = [v for v in valores if not math.isnan(v)]
    return sum(con_dato) if con_dato else VACIO


def _comunes(año):
    # Los campos que llevan los tres estados.
    campos = ["symbol", "date", "fiscalYear", "reportedCurrency"]
    return {campo: año[campo] for campo in campos}


def get_balance_sheet(symbol, limit=5):
    balances = []
    for año in _años(symbol, limit):
        # Deuda financiera = no corriente + corriente. Si la empresa no da la
        # deuda corriente total, se suman sus piezas.
        corriente = año["deudaCorriente"]
        if math.isnan(corriente):
            corriente = _sumar(
                año["deudaLargoQueVence"],
                año["pagares"],
                año["prestamosCorto"],
                año["otrosPrestamosCorto"],
            )
        balances.append(
            _comunes(año)
            | {
                "totalAssets": año["totalAssets"],
                "totalLiabilitiesAndTotalEquity": año["totalLiabilitiesAndTotalEquity"],
                "totalStockholdersEquity": año["totalStockholdersEquity"],
                "totalCurrentAssets": año["totalCurrentAssets"],
                "totalCurrentLiabilities": año["totalCurrentLiabilities"],
                "inventory": año["inventory"],
                "cashAndCashEquivalents": año["cashAndCashEquivalents"],
                "totalDebt": _sumar(año["deudaNoCorriente"], corriente),
            }
        )
    return balances


def get_income_statement(symbol, limit=5):
    resultados = []
    for año in _años(symbol, limit):
        # Muchas empresas no presentan el beneficio bruto: ventas - coste.
        bruto = año["grossProfit"]
        if math.isnan(bruto):
            bruto = año["revenue"] - año["costeVentas"]
        resultados.append(
            _comunes(año)
            | {
                "revenue": año["revenue"],
                "grossProfit": bruto,
                "operatingIncome": año["operatingIncome"],
                "netIncome": año["netIncome"],
            }
        )
    return resultados


def get_cash_flow_statement(symbol, limit=5):
    flujos = []
    for año in _años(symbol, limit):
        flujos.append(
            _comunes(año)
            | {
                "operatingCashFlow": año["operatingCashFlow"],
                # La SEC da el capex como pago (positivo); el motor lo espera
                # en negativo (salida de caja), como lo daba FMP.
                "capitalExpenditure": -año["pagosCapex"],
            }
        )
    return flujos
