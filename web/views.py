import math

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render

from src.data.sec_client import url_10k
from src.financial.ratios import NOMBRES_RATIOS, calcular_medianas_sector
from src.formato import formatear
from src.pipeline import (
    explicar_empresa,
    listar_empresas,
    obtener_comparacion,
    obtener_perfil,
    obtener_ratios,
)


def _ruta_db():
    return str(settings.RUTA_DUCKDB)


def _empresas_disponibles():
    # Sin archivo de DuckDB no hay datos (y así no se crea uno vacío).
    if not settings.RUTA_DUCKDB.exists():
        return []
    return listar_empresas(_ruta_db())


# Partidas de los estados financieros que se enseñan, por estado. Son las
# cifras de la SEC con las que se calculan los ratios (ya están en la tabla
# que devuelve obtener_ratios: no hace falta otra consulta).
PARTIDAS = {
    "Balance": {
        "total_assets": "Activo total",
        "total_current_assets": "Activo corriente",
        "cash_and_cash_equivalents": "Caja y equivalentes",
        "inventory": "Inventario",
        "total_current_liabilities": "Pasivo corriente",
        "total_debt": "Deuda total",
        "total_stockholders_equity": "Patrimonio neto",
    },
    "Cuenta de resultados": {
        "revenue": "Ventas",
        "gross_profit": "Beneficio bruto",
        "operating_income": "Resultado operativo",
        "net_income": "Beneficio neto",
    },
    "Flujos de caja": {
        "operating_cash_flow": "Flujo de caja operativo",
        "capital_expenditure": "Inversión en activo fijo (capex)",
        "flujo_caja_libre": "Flujo de caja libre (calculado)",
    },
}


def _millones(valor):
    # 391035000000 -> "391.035" (millones, con punto de miles). "—" si falta.
    if valor is None or math.isnan(valor):
        return "—"
    return f"{valor / 1e6:,.0f}".replace(",", ".")


def _minigrafico(valores, ancho=100, alto=24):
    # Puntos "x,y" de la línea que dibuja la evolución de un ratio en un SVG.
    # Solo es dibujo: reescala cifras ya calculadas al tamaño del gráfico
    # (el valor más bajo abajo, el más alto arriba). Los años "—" se saltan.
    puntos = [(i, v) for i, v in enumerate(valores) if not math.isnan(v)]
    if len(puntos) < 2:
        return ""
    minimo = min(v for _, v in puntos)
    rango = max(v for _, v in puntos) - minimo or 1
    paso = ancho / (len(valores) - 1)
    return " ".join(
        f"{i * paso:.1f},{alto - (v - minimo) / rango * alto:.1f}" for i, v in puntos
    )


def _formatear_perfil(perfil):
    # Solo presentación: el PER ya llega calculado desde src/.
    return {
        "nombre": perfil["company_name"],
        "sector": perfil["sector"],
        "industria": perfil["industry"],
        "moneda": perfil["currency"],
        "precio": formatear("precio", perfil["price"]),
        "variacion": f"{perfil['change_percentage']:+.2f} %".replace(".", ","),
        "capitalizacion": f"{_millones(perfil['market_cap'])} M",
        "per": formatear("per", perfil["per"]),
        "fecha": perfil["date"],
    }


def inicio(request):
    # Una tarjeta por empresa con sus cifras clave, agrupadas por sector (la
    # plantilla las agrupa con regroup: llegan ordenadas por sector).
    datos = obtener_comparacion(_ruta_db()) if _empresas_disponibles() else []
    tarjetas = [
        {
            "symbol": fila["symbol"],
            "nombre": fila["nombre"],
            "sector": fila["sector"],
            "precio": f"{formatear('precio', fila['precio'])} {fila['moneda']}",
            "per": formatear("per", fila["per"]),
            "crecimiento": formatear("crecimiento_ventas", fila["crecimiento_ventas"]),
            "ejercicio": fila["fiscal_year"],
        }
        for fila in datos
    ]
    return render(request, "web/inicio.html", {"tarjetas": tarjetas})


def empresa(request, symbol):
    symbol = symbol.upper()
    if symbol not in _empresas_disponibles():
        raise Http404(f"No hay datos guardados de {symbol}.")

    ratios = obtener_ratios([symbol], _ruta_db())
    perfil = obtener_perfil(symbol, _ruta_db())

    # La explicación de la IA solo se pide al pulsar el botón (?explicar=1):
    # tarda unos segundos y usa la API de Gemini.
    explicacion, modelo, dudosas = None, None, []
    if "explicar" in request.GET:
        try:
            explicacion, modelo, dudosas = explicar_empresa(symbol, _ruta_db())
        except RuntimeError as error:
            explicacion = f"No se pudo generar la explicación: {error}"

    # Misma forma que en la terminal: una fila por ratio, una columna por año.
    filas = [
        {
            "nombre": nombre,
            "valores": [formatear(columna, valor) for valor in ratios[columna]],
            "puntos": _minigrafico(ratios[columna].tolist()),
        }
        for columna, nombre in NOMBRES_RATIOS.items()
    ]

    # Igual para los estados financieros, en millones y agrupados por estado.
    estados = [
        {
            "nombre": estado,
            "filas": [
                {"nombre": nombre, "valores": [_millones(v) for v in ratios[columna]]}
                for columna, nombre in partidas.items()
            ],
        }
        for estado, partidas in PARTIDAS.items()
    ]

    contexto = {
        "symbol": symbol,
        "moneda": ratios["reported_currency"].iloc[0],
        "ejercicios": ratios["fiscal_year"].tolist(),
        "filas": filas,
        "estados": estados,
        "fuente": ratios["fuente"].iloc[0],
        "url_10k": url_10k(symbol),
        "extraccion": ratios["fecha_extraccion_utc"].max(),
        "perfil": _formatear_perfil(perfil) if perfil else None,
        "explicacion": explicacion,
        "modelo": modelo,
        "dudosas": dudosas,
    }
    return render(request, "web/empresa.html", contexto)


def empresa_csv(request, symbol):
    # Los ratios de la empresa en un archivo CSV para abrir en Excel: una fila
    # por ejercicio y una columna por ratio. Cifras tal cual las calcula
    # ratios.py (porcentajes en tanto por uno: 0,25 = 25 %).
    symbol = symbol.upper()
    if symbol not in _empresas_disponibles():
        raise Http404(f"No hay datos guardados de {symbol}.")

    ratios = obtener_ratios([symbol], _ruta_db())
    tabla = ratios[["fiscal_year", *NOMBRES_RATIOS]].rename(
        columns={"fiscal_year": "Ejercicio", **NOMBRES_RATIOS}
    )
    # ";" y coma decimal: es lo que espera Excel en español. "﻿" al
    # principio le dice a Excel que el texto es UTF-8 (si no, rompe las tildes).
    texto = tabla.to_csv(index=False, sep=";", decimal=",", float_format="%.4f")
    respuesta = HttpResponse("﻿" + texto, content_type="text/csv; charset=utf-8")
    # "attachment": el navegador lo descarga en vez de enseñarlo.
    respuesta["Content-Disposition"] = f'attachment; filename="{symbol}_ratios.csv"'
    return respuesta


def _clave_orden(fila, columna):
    # Para sorted(): primero el sector; dentro, los que tienen dato antes que
    # los "—" (False va antes que True), y de mayor a menor (por eso el "-").
    valor = fila[columna]
    vacio = math.isnan(valor)
    return (fila["sector"], vacio, 0 if vacio else -valor)


def comparar(request):
    # Una fila por empresa (su último ejercicio) y una columna por ratio.
    columnas = {"per": "PER", **NOMBRES_RATIOS}
    datos = obtener_comparacion(_ruta_db()) if _empresas_disponibles() else []
    medianas = calcular_medianas_sector(datos, list(columnas))

    # ?orden=roe: dentro de cada sector, de mayor a menor ROE (los "—" al
    # final). Se ordena sin salir del sector para que la mediana siga debajo.
    orden = request.GET.get("orden")
    if orden in columnas:
        datos = sorted(datos, key=lambda fila: _clave_orden(fila, orden))

    # Las empresas llegan ordenadas por sector: al acabar cada sector que
    # tenga mediana, se añade su fila "Mediana del sector".
    filas = []
    for i, fila in enumerate(datos):
        filas.append(
            {
                "symbol": fila["symbol"],
                "sector": fila["sector"],
                "ejercicio": fila["fiscal_year"],
                "valores": [formatear(columna, fila[columna]) for columna in columnas],
            }
        )
        acaba_el_sector = (
            i + 1 == len(datos) or datos[i + 1]["sector"] != fila["sector"]
        )
        if acaba_el_sector and fila["sector"] in medianas:
            mediana = medianas[fila["sector"]]
            filas.append(
                {
                    "es_mediana": True,
                    "sector": fila["sector"],
                    "valores": [
                        formatear(columna, mediana[columna]) for columna in columnas
                    ],
                }
            )
    return render(
        request,
        "web/comparar.html",
        {"columnas": columnas.items(), "filas": filas, "orden": orden},
    )
