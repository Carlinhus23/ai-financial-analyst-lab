import math

from django.conf import settings
from django.http import Http404
from django.shortcuts import render

from src.financial.ratios import NOMBRES_RATIOS
from src.pipeline import (
    listar_empresas,
    obtener_comparacion,
    obtener_perfil,
    obtener_ratios,
)

# Cómo se muestra cada ratio. Es solo presentación: las cifras llegan ya
# calculadas desde src/ y aquí no se hace ninguna cuenta financiera.
RATIOS_EN_PORCENTAJE = {
    "deuda_sobre_activos",
    "margen_bruto",
    "margen_operativo",
    "margen_neto",
    "roa",
    "roe",
    "margen_fcf",
}


def _ruta_db():
    return str(settings.RUTA_DUCKDB)


def _empresas_disponibles():
    # Sin archivo de DuckDB no hay datos (y así no se crea uno vacío).
    if not settings.RUTA_DUCKDB.exists():
        return []
    return listar_empresas(_ruta_db())


def _formatear(columna, valor):
    if valor is None or math.isnan(valor):
        return "—"
    if columna in RATIOS_EN_PORCENTAJE:
        return f"{valor * 100:.1f} %".replace(".", ",")
    return f"{valor:.2f}".replace(".", ",")


def _formatear_perfil(perfil):
    # Solo presentación: el PER ya llega calculado desde src/.
    millones = f"{perfil['market_cap'] / 1e6:,.0f}".replace(",", ".")
    return {
        "nombre": perfil["company_name"],
        "sector": perfil["sector"],
        "industria": perfil["industry"],
        "moneda": perfil["currency"],
        "precio": f"{perfil['price']:.2f}".replace(".", ","),
        "variacion": f"{perfil['change_percentage']:+.2f} %".replace(".", ","),
        "capitalizacion": f"{millones} M",
        "per": _formatear("per", perfil["per"]),
        "fecha": perfil["date"],
    }


def inicio(request):
    return render(request, "web/inicio.html", {"empresas": _empresas_disponibles()})


def empresa(request, symbol):
    symbol = symbol.upper()
    if symbol not in _empresas_disponibles():
        raise Http404(f"No hay datos guardados de {symbol}.")

    ratios = obtener_ratios([symbol], _ruta_db())
    perfil = obtener_perfil(symbol, _ruta_db())

    # Misma forma que en la terminal: una fila por ratio, una columna por año.
    filas = [
        {
            "nombre": nombre,
            "valores": [_formatear(columna, valor) for valor in ratios[columna]],
        }
        for columna, nombre in NOMBRES_RATIOS.items()
    ]

    contexto = {
        "symbol": symbol,
        "moneda": ratios["reported_currency"].iloc[0],
        "ejercicios": ratios["fiscal_year"].tolist(),
        "filas": filas,
        "fuente": ratios["fuente"].iloc[0],
        "extraccion": ratios["fecha_extraccion_utc"].max(),
        "perfil": _formatear_perfil(perfil) if perfil else None,
    }
    return render(request, "web/empresa.html", contexto)


def comparar(request):
    # Una fila por empresa (su último ejercicio) y una columna por ratio.
    columnas = {"per": "PER", **NOMBRES_RATIOS}
    datos = obtener_comparacion(_ruta_db()) if _empresas_disponibles() else []
    filas = [
        {
            "symbol": fila["symbol"],
            "sector": fila["sector"],
            "ejercicio": fila["fiscal_year"],
            "valores": [_formatear(columna, fila[columna]) for columna in columnas],
        }
        for fila in datos
    ]
    return render(
        request,
        "web/comparar.html",
        {"columnas": columnas.values(), "filas": filas},
    )
