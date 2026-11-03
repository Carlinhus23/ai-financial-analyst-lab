# AI Financial Analyst

Trabajo Fin de Grado (Finanzas + RRLL y RRHH, Universidad de Sevilla).

Analista financiero asistido por IA: descarga los estados financieros oficiales
de [SEC EDGAR](https://www.sec.gov/edgar) (cuentas anuales 10-K) y la cotización
de Yahoo Finance (librería `yfinance`), los limpia, valida y guarda en DuckDB, y calcula ratios con código determinista y probado.
Un LLM (Gemini, plan gratuito de su API) explica las métricas ya calculadas: **el
LLM nunca calcula cifras**; solo recibe la ficha con las cifras de la web.

## Puesta en marcha (Windows)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env   # y pon tu nombre y email en SEC_USER_AGENT (lo exige la SEC)
# en GEMINI_API_KEY tu clave de aistudio.google.com (gratis)
# y en DJANGO_SECRET_KEY el resultado de:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
python manage.py migrate # crea la base interna de Django (db.sqlite3)
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
python main.py    # descarga balance, resultados y flujos (5 años) y cotización de 12 empresas y muestra sus ratios
python manage.py runserver   # web local en http://127.0.0.1:8000/ (lee lo ya descargado)
pytest            # tests (no llaman a internet)
ruff check .      # revisa el código
ruff format .     # da formato al código
```

## Estructura

```
main.py                    punto de entrada: elige empresas y muestra resultados
src/pipeline.py            orquesta el motor: actualizar_empresa(), obtener_ratios()
src/data/sec_client.py     estados financieros de la SEC (traduce las etiquetas XBRL)
src/data/yahoo_client.py   perfil y cotización de Yahoo Finance
src/data/transformer.py    JSON -> DataFrame y trazabilidad
src/data/validator.py      comprobaciones antes de guardar
src/database/duckdb_manager.py   SQL: guardar (acumulando), leer y unir los 3 estados
src/financial/ratios.py    fórmulas de los ratios (sin LLM)
src/formato.py             cómo se escribe cada cifra (web y LLM ven lo mismo)
src/llm/explicador.py      el LLM (Gemini) explica la ficha de una empresa
config/                    configuración de Django (settings, urls)
web/                       app de Django: vistas y plantillas; solo llama a src/pipeline.py
docs/decisiones.md         decisiones de diseño y sus motivos
tests/                     tests con pytest (incluida la web, con pytest-django)
learning/                  scripts de aprendizaje; no forman parte del motor
```

`src/` es Python puro: no depende de ninguna interfaz web. No ejecutes
`python main.py` con la web encendida: DuckDB no deja escribir mientras otro
proceso tiene la base abierta.

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
| PER | `capitalización / net_income` (último ejercicio) | `NaN` (también si el beneficio ≤ 0) |
| Flujo de caja libre | `operating_cash_flow + capital_expenditure` (capex en negativo) | — |
| Margen FCF | `flujo_caja_libre / revenue` | `NaN` |
| Calidad del beneficio | `operating_cash_flow / net_income` | `NaN` (también si el beneficio ≤ 0) |

ROA y ROE usan el balance de cierre del año, no la media del año
(simplificación).

## Trazabilidad

Cada fila guardada lleva `symbol`, `date` (cierre del ejercicio), `fiscal_year` y
`reported_currency`, más `fuente` ("SEC EDGAR (10-K)" o "Yahoo Finance") y
`fecha_extraccion_utc` (añadidas por el pipeline). Los importes van en dólares,
no en miles. Cómo se traduce cada partida de la SEC: `src/data/sec_client.py` y
`docs/decisiones.md`.
La base de datos acumula: volver a descargar una empresa sustituye sus filas
por (`symbol`, `date`) sin tocar las demás.
