# AI Financial Analyst (TFG)

Analista financiero asistido por IA. Recupera estados financieros (Financial Modeling Prep), los limpia y valida, los guarda, calcula ratios con código determinista y, más adelante, un LLM interpreta métricas ya calculadas. Es el TFG de Carlos (Finanzas + RRLL y RRHH, Universidad de Sevilla). Idioma de trabajo: español.

## Principio de diseño (no negociable)
El LLM nunca calcula cifras ni ratios. Las fórmulas viven en Python/pandas, con tests. El LLM solo explica métricas ya calculadas y no inventa números.

## Arquitectura
FMP API -> `src/data/fmp_client.py` -> `transformer.py` (pandas, snake_case) -> `validator.py` -> persistencia (`src/database/duckdb_manager.py`) -> `src/financial/ratios.py` -> (futuro) capa LLM -> (futuro) interfaz Django.

Regla: `src/` es Python puro y no importa Django. Django (cuando llegue) solo llama a `src/`. Así el motor se prueba sin web y la web es sustituible.

## Cómo enseñar a Carlos (importante)
- Carlos está aprendiendo programación construyendo este proyecto real. Nada de ejercicios aislados.
- Primero haz el cambio real. Después explícalo ligado a ese cambio: qué problema resuelve, dónde encaja en la arquitectura, y cómo comprobarlo. Un concepto nuevo = 1-3 frases.
- No expliques línea a línea. No re-expliques lo que ya conoce: variables, funciones, imports, if/raise ValueError, list comprehensions, DataFrame, columnas, df.copy(), assert, SELECT/WHERE/GROUP BY, conexión DuckDB, .env y flujo git pull/add/commit/push.
- Si pregunta "por qué" o "cómo funciona", entonces sí profundiza.
- Tono cercano y profesional, sin paternalismo. Avanza en pasos pequeños: pocos archivos y conceptos por sesión.
- Distingue siempre lo confirmado (ejecutado y visto) de lo propuesto. No des por hecho un paso que no se ha probado.

## Cómo trabajar
- Antes de cambios grandes (nueva dependencia, mover archivos, refactor), explica el plan en pocas líneas y espera el visto bueno.
- Tras cambiar código, ejecuta las pruebas y enseña el resultado real. Si falla, depura con el mensaje completo, no con suposiciones.
- Commits solo cuando Carlos lo pida. Mensajes en inglés, imperativo y concretos (ej.: `Add debt-to-assets ratio`).
- Carlos trabaja en dos ordenadores Windows: empezar con `.\inicio.ps1` (pull + deps + tests), terminar con `.\fin.ps1 "mensaje"` (tests + ruff + commit + push; no sube si algo falla). Ejecutar `fin.ps1` es la forma en que Carlos pide el commit.

## Seguridad
- Nunca leas, imprimas ni pidas la clave API. `.env` está en `.gitignore` y no se sube. Mantén un `.env.example` solo con nombres de variables.

## Comandos conocidos
- Pipeline completo: `python main.py` (desde la raíz). Hace 9 llamadas a FMP (3 por empresa).
- Python del proyecto: `.\.venv\Scripts\python.exe` (el `python` global no tiene las dependencias).
- Tests: `pytest` (config en `pyproject.toml`: solo recoge `tests/`, porque `learning/` tiene scripts `*_test.py` que llaman a la API real). Ningún test llama a FMP.
- Linter: `ruff check .` (y `--fix`), formato: `ruff format .`. Config en `pyproject.toml`; excluye `learning/`.
- Instalar dependencias: `python -m pip install -r requirements.txt`.
- Ojo (Windows PowerShell 5.1): no reescribir archivos UTF-8 con `Get-Content`/`Set-Content`, corrompe las tildes. Usar las herramientas de edición o Python.

## Estado (revisado el 11-10-2026 ejecutando) — CHECKPOINT 1
- Confirmado: `python main.py` funciona de punta a punta para AAPL, MSFT y KO (5 años cada una): API -> DataFrame -> trazabilidad -> validación -> DuckDB (acumulando) -> lectura -> unión balance+resultados -> 10 ratios.
- Confirmado (16-10-2026): flujos de caja añadidos; `python main.py` OK con 9 llamadas; `pytest` pasa 59/59 y `ruff check .` limpio.
- Arquitectura actual: `main.py` solo elige empresas y muestra; `src/pipeline.py` orquesta (`actualizar_empresa`, `obtener_ratios`); Django llamará a `src/pipeline.py` en el futuro.
- `fmp_client.py`: `get_balance_sheet`, `get_income_statement`, `get_cash_flow_statement` (comparten `_get_estado_financiero`).
- `transformer.py`: `estado_a_dataframe` (antes `balance_sheet_a_dataframe`), `añadir_trazabilidad`. (`unir_estados` en pandas se eliminó: la unión ahora es SQL.)
- `validator.py`: `validar_balance`, `validar_cuenta_resultados`, `validar_flujos_caja` (comparten `_validar_comun`; `_comprobar_cuadre` verifica deuda neta y FCF de FMP contra nuestro cálculo; el capex debe llegar en negativo).
- `duckdb_manager.py`: `guardar_estado(df, tabla)` borra e inserta solo las (symbol, date) que trae, en transacción; `obtener_estado(tabla, symbols)`. Tablas permitidas: `balance_sheet`, `income_statement`, `cash_flow_statement`. `obtener_datos_analisis(symbols)`: INNER JOIN de los 3 estados por symbol+date con columnas explícitas (`b.inventory` = saldo del balance) y error si salen periodos duplicados.
- Reparto acordado con Carlos: SQL para los datos (guardar, filtrar, unir); Python para fórmulas, limpieza y validación.
- Ratios: deuda/activos, deuda/patrimonio, liquidez corriente, prueba ácida, ratio de caja, márgenes bruto/operativo/neto, ROA, ROE, flujo de caja libre (OCF + capex, calculado por nosotros), margen FCF, calidad del beneficio (OCF / beneficio neto; NaN si beneficio <= 0). ROA/ROE con balance de cierre (no media).
- Política de ratios: denominador 0 o nulo -> NaN (`_dividir`). Con patrimonio <= 0 también NaN (`_dividir_si_positivo`, para deuda/patrimonio y ROE).
- FMP da `interest_expense = 0` para AAPL: no fiarse de ese campo (por eso no hay cobertura de intereses).
- `*.duckdb` en `.gitignore`: la base se regenera con `python main.py` y no se sube.
- `docs/decisiones.md`: registro de decisiones (LLM no calcula; SQL datos / Python fórmulas; Django lee del motor, sin ORM para datos financieros).
- Django 6.1.2 (fase 2 iniciada 16-10-2026): `config/` (settings lee `DJANGO_SECRET_KEY` de `.env`; `RUTA_DUCKDB`), app `web/` con `inicio` (`/`, lista empresas) y `empresa` (`/empresa/<symbol>/`, tabla de ratios). Las vistas solo llaman a `src/pipeline.py` (`listar_empresas`, `obtener_ratios`) y solo formatean (%, coma decimal). Nombres de ratios en `NOMBRES_RATIOS` (`ratios.py`), compartidos con `main.py`. Tests de la web en `tests/test_web.py` (pytest-django, fixture `settings`); datos falsos de FMP en `tests/conftest.py`.
- Web local: `python manage.py runserver`. No ejecutar `main.py` con la web abierta (bloqueo de DuckDB).
- Carpeta de trabajo en este ordenador: `Desktop\AI FINANCIAL ANALYST`.

## Siguiente paso
1. Repaso guiado: hechos fmp_client y transformer. El resto (validator -> duckdb_manager -> ratios -> pipeline -> main -> tests) lo estudia Carlos por su cuenta; explicar bloque a bloque solo si lo pide.
2. Django en marcha: ya hay página de inicio y tabla por empresa. Carlos la ve fea: lo primero de la próxima sesión es mejorar el aspecto (CSS propio en `web/static/` o una hoja ligera tipo Pico.css; sin herramientas de compilación). Después, ideas: comparar empresas en una tabla, mostrar los estados financieros (no solo ratios), botón para actualizar desde la web (cuidado con el bloqueo de DuckDB).

## Riesgos conocidos a resolver
- Conservar `symbol` y `date` en todo para no mezclar empresas o periodos.
- No sacar conclusiones tipo "deuda alta/baja" con umbrales arbitrarios: depende del sector.

## Hoja de ruta
0. ~~Cimientos: pytest, `requirements.txt`/`pyproject.toml`, `.env.example`, README, linter.~~ Hecho.
1. ~~Cerrar el núcleo: ratio de deuda/activos con tests, validaciones robustas, más ratios.~~ Hecho (checkpoint 1).
2. Django: proyecto `config/` + app `web/`, modelos (Company, Statement/Period, Ratio), primera página con la tabla de Apple. Decidir aquí si la persistencia pasa al ORM de Django (ver `docs/decisiones.md`).
3. Más empresas y estados (cuenta de resultados, flujos), comparativas.
4. Capa LLM sobre métricas ya calculadas.
5. Cierre TFG: documentación, tests, demo reproducible en local, despliegue opcional.
