# AI Financial Analyst

Trabajo Fin de Grado (Finanzas + RRLL y RRHH, Universidad de Sevilla).

Analista financiero asistido por IA: descarga estados financieros de
[Financial Modeling Prep](https://site.financialmodelingprep.com/), los limpia,
valida y guarda en DuckDB, y calcula ratios con código determinista y probado.
En fases posteriores, un LLM interpretará las métricas ya calculadas: **el LLM
nunca calcula cifras**.

## Puesta en marcha (Windows)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env   # y pon tu clave de FMP en API_KEY
```

## Rutina de trabajo (dos ordenadores)

```powershell
.\inicio.ps1                     # al empezar: git pull + dependencias + tests
.\fin.ps1                        # al terminar: tests + ruff + commit + push
.\fin.ps1 "Add cash flow ratios" # igual, con el mensaje ya puesto
```

`fin.ps1` no sube nada si fallan los tests o ruff. Si Windows bloquea los
scripts, ejecuta una vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

## Uso

```powershell
python main.py    # descarga balance, resultados y flujos de AAPL, MSFT y KO (5 años) y muestra sus ratios
pytest            # tests (no llaman a la API)
ruff check .      # revisa el código
ruff format .     # da formato al código
```

## Estructura

```
main.py                    punto de entrada: elige empresas y muestra resultados
src/pipeline.py            orquesta el motor: actualizar_empresa(), obtener_ratios()
src/data/fmp_client.py     descarga de la API de FMP
src/data/transformer.py    JSON -> DataFrame y trazabilidad
src/data/validator.py      comprobaciones antes de guardar
src/database/duckdb_manager.py   SQL: guardar (acumulando), leer y unir los 3 estados
src/financial/ratios.py    fórmulas de los ratios (sin LLM)
tests/                     tests con pytest
learning/                  scripts de aprendizaje; no forman parte del motor
```

`src/` es Python puro: no depende de ninguna interfaz web.

## Ratios disponibles

| Ratio | Fórmula | Si el denominador es 0 o falta |
|---|---|---|
| Deuda sobre activos | `total_debt / total_assets` | `NaN` |
| Deuda sobre patrimonio | `total_debt / total_stockholders_equity` | `NaN` (también si el patrimonio ≤ 0) |
| Liquidez corriente | `total_current_assets / total_current_liabilities` | `NaN` |
| Prueba ácida | `(total_current_assets - inventory) / total_current_liabilities` | `NaN` |
| Ratio de caja | `cash_and_cash_equivalents / total_current_liabilities` | `NaN` |
| Margen bruto | `gross_profit / revenue` | `NaN` |
| Margen operativo | `operating_income / revenue` | `NaN` |
| Margen neto | `net_income / revenue` | `NaN` |
| ROA | `net_income / total_assets` | `NaN` |
| ROE | `net_income / total_stockholders_equity` | `NaN` (también si el patrimonio ≤ 0) |
| Flujo de caja libre | `operating_cash_flow + capital_expenditure` (capex en negativo) | — |
| Margen FCF | `flujo_caja_libre / revenue` | `NaN` |
| Calidad del beneficio | `operating_cash_flow / net_income` | `NaN` (también si el beneficio ≤ 0) |

ROA y ROE usan el balance de cierre del año, no la media del año
(simplificación).

## Trazabilidad

Cada fila guardada lleva `symbol`, `date`, `fiscal_year`, `period` y
`reported_currency` (de FMP), más `fuente` y `fecha_extraccion_utc` (añadidas
por el pipeline). FMP da los importes en unidades de la moneda, no en miles.
La base de datos acumula: volver a descargar una empresa sustituye sus filas
por (`symbol`, `date`) sin tocar las demás.
