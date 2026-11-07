import math

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render

from src.data.sec_client import url_10k
from src.financial.ratios import (
    FORMULAS_RATIOS,
    GRUPOS_RATIOS,
    NOMBRES_RATIOS,
    calcular_medianas_sector,
)
from src.formato import formatear
from src.pipeline import (
    comparar_empresas,
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


# Ratios que son variaciones (suben o bajan respecto al año anterior): solo
# estos llevan color. Un ratio normal no se colorea, porque si es "bueno" o
# "malo" depende del sector.
COLUMNAS_CON_SIGNO = {"crecimiento_ventas", "crecimiento_beneficio"}


def _signo(valor):
    # Clase CSS según el signo de una variación: "sube" (verde) o "baja"
    # (rojo). Sin dato o exactamente 0, sin color.
    if valor is None or math.isnan(valor) or valor == 0:
        return ""
    return "sube" if valor > 0 else "baja"


def _formatear_perfil(perfil):
    # Solo presentación: el PER ya llega calculado desde src/.
    return {
        "nombre": perfil["company_name"],
        "sector": perfil["sector"],
        "industria": perfil["industry"],
        "moneda": perfil["currency"],
        "precio": formatear("precio", perfil["price"]),
        "variacion": f"{perfil['change_percentage']:+.2f} %".replace(".", ","),
        "signo_variacion": _signo(perfil["change_percentage"]),
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
            "signo": _signo(fila["crecimiento_ventas"]),
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

    # Mediana de su sector (último ejercicio de cada empresa), calculada en
    # src/ como en Comparar. None si su sector tiene una sola empresa.
    sector = perfil["sector"] if perfil else None
    medianas = calcular_medianas_sector(
        obtener_comparacion(_ruta_db()), list(NOMBRES_RATIOS)
    )
    mediana = medianas.get(sector)

    # Una fila por ratio y una columna por año, agrupadas en bloques
    # (endeudamiento, liquidez...) con su título.
    grupos = [
        {
            "nombre": grupo,
            "filas": [
                {
                    "nombre": NOMBRES_RATIOS[columna],
                    "formula": FORMULAS_RATIOS[columna],
                    # (texto, clase de color): color solo en las variaciones.
                    "valores": [
                        (
                            formatear(columna, v),
                            _signo(v) if columna in COLUMNAS_CON_SIGNO else "",
                        )
                        for v in ratios[columna]
                    ],
                    "puntos": _minigrafico(ratios[columna].tolist()),
                    "mediana": formatear(columna, mediana[columna]) if mediana else "",
                }
                for columna in columnas
            ],
        }
        for grupo, columnas in GRUPOS_RATIOS.items()
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
        "grupos": grupos,
        # Sector con mediana (la plantilla añade la columna solo si lo hay) y
        # columnas totales de la tabla, para que los títulos de bloque la crucen.
        "sector_mediana": sector if mediana else None,
        "columnas_tabla": len(ratios) + (3 if mediana else 2),
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


def metodologia(request):
    # Cómo se calcula todo, para quien quiera comprobarlo. Las fórmulas salen
    # de FORMULAS_RATIOS (las mismas que se ven al pasar el ratón): no se
    # escriben dos veces.
    grupos = [
        {
            "nombre": grupo,
            "ratios": [(NOMBRES_RATIOS[c], FORMULAS_RATIOS[c]) for c in columnas],
        }
        for grupo, columnas in GRUPOS_RATIOS.items()
    ]
    return render(request, "web/metodologia.html", {"grupos": grupos})


def comparar_ia(request):
    # La IA compara dos empresas elegidas en el formulario de Comparar
    # (/comparar/ia/?a=AAPL&b=MSFT). Solo empresas con datos y distintas.
    disponibles = _empresas_disponibles()
    a = request.GET.get("a", "").upper()
    b = request.GET.get("b", "").upper()
    if a not in disponibles or b not in disponibles or a == b:
        raise Http404("Elige dos empresas distintas con datos guardados.")

    explicacion, modelo, dudosas = None, None, []
    try:
        explicacion, modelo, dudosas = comparar_empresas(a, b, _ruta_db())
    except RuntimeError as error:
        explicacion = f"No se pudo generar la comparación: {error}"

    contexto = {
        "a": a,
        "b": b,
        "explicacion": explicacion,
        "modelo": modelo,
        "dudosas": dudosas,
    }
    return render(request, "web/comparar_ia.html", contexto)
