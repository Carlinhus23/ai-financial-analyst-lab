# AI Financial Analyst (TFG) — LABORATORIO

> ESTA CARPETA ES EL LABORATORIO (fork), no el proyecto principal. Repo: `ai-financial-analyst-lab` (remoto `origin`); el principal es el remoto `principal`. Aquí Claude hace mejoras experimentales en un loop y Carlos decide cuáles pasan al principal. Reglas del loop, cola de ideas e ids de la guía: `LABORATORIO.md` (leerlo antes de cada vuelta). Aquí SÍ se hace commit + push de cada mejora (Carlos lo autorizó el 07-11-2026); en el principal siguen las reglas de siempre.

Analista financiero asistido por IA. Recupera estados financieros oficiales (SEC EDGAR, 10-K) y la cotización (Yahoo Finance, `yfinance`), los limpia y valida, los guarda, calcula ratios con código determinista y un LLM (Gemini, API gratuita) explica las métricas ya calculadas. Es el TFG de Carlos (Finanzas + RRLL y RRHH, Universidad de Sevilla). Idioma de trabajo: español.

## Principio de diseño (no negociable)
El LLM nunca calcula cifras ni ratios. Las fórmulas viven en Python/pandas, con tests. El LLM solo explica métricas ya calculadas y no inventa números.

## Arquitectura
SEC EDGAR -> `src/data/sec_client.py` (+ Yahoo -> `yahoo_client.py` para el perfil) -> `transformer.py` (pandas, snake_case) -> `validator.py` -> persistencia (`src/database/duckdb_manager.py`) -> `src/financial/ratios.py` -> `src/llm/explicador.py` (Gemini) -> interfaz Django (`web/`).

Regla: `src/` es Python puro y no importa Django. Django (cuando llegue) solo llama a `src/`. Así el motor se prueba sin web y la web es sustituible.

## Cómo enseñar a Carlos (importante)
- Carlos está aprendiendo programación construyendo este proyecto real. Nada de ejercicios aislados.
- Primero haz el cambio real. Después explícalo ligado a ese cambio: qué problema resuelve, dónde encaja en la arquitectura, y cómo comprobarlo. Un concepto nuevo = 1-3 frases.
- No expliques línea a línea. No re-expliques lo que ya conoce: variables, funciones, imports, if/raise ValueError, list comprehensions, DataFrame, columnas, df.copy(), assert, SELECT/WHERE/GROUP BY, conexión DuckDB, .env y flujo git pull/add/commit/push.
- Si pregunta "por qué" o "cómo funciona", entonces sí profundiza.
- Tono cercano y profesional, sin paternalismo. Avanza en pasos pequeños: pocos archivos y conceptos por sesión.
- Distingue siempre lo confirmado (ejecutado y visto) de lo propuesto. No des por hecho un paso que no se ha probado.

## Cómo trabajar
- REGLA (Carlos, 03-11-2026): todo cambio de código se refleja también en la guía de estudio (Claude Doc), en sus DOS pestañas: la de bloques y "Línea a línea" (con los números de línea al día). Antes de editarla, leer con `sinceRev` por si Carlos la cambió.
- Antes de cambios grandes (nueva dependencia, mover archivos, refactor), explica el plan en pocas líneas y espera el visto bueno.
- Tras cambiar código, ejecuta las pruebas y enseña el resultado real. Si falla, depura con el mensaje completo, no con suposiciones.
- Commits solo cuando Carlos lo pida. Mensajes en inglés, imperativo y concretos (ej.: `Add debt-to-assets ratio`).
- Carlos trabaja en dos ordenadores Windows: empezar con `.\inicio.ps1` (pull + deps + tests), terminar con `.\fin.ps1 "mensaje"` (tests + ruff + commit + push; no sube si algo falla). Ejecutar `fin.ps1` es la forma en que Carlos pide el commit.

## Seguridad
- Nunca leas ni imprimas `.env`. Está en `.gitignore` y no se sube. Mantén un `.env.example` solo con nombres de variables. Ya no hay clave de FMP: `.env` tiene `SEC_USER_AGENT` (nombre y email de Carlos, lo exige la SEC; añadido con su permiso el 03-11-2026), `DJANGO_SECRET_KEY` y `GEMINI_API_KEY` (clave gratuita de Google AI Studio que creó Carlos). Comprobar claves sin leer ni imprimir valores (`dotenv_values`), y la de Gemini va en la cabecera `x-goog-api-key`, nunca en la URL.

## Comandos conocidos
- Pipeline completo: `python main.py` (desde la raíz). Por empresa: 1 descarga de la SEC (los 3 estados) + 1 de Yahoo (perfil), más 1 de la tabla de tickers por ejecución. Sin límite diario.
- Python del proyecto: `.\.venv\Scripts\python.exe` (el `python` global no tiene las dependencias).
- Tests: `pytest` (config en `pyproject.toml`: solo recoge `tests/`, porque `learning/` tiene scripts `*_test.py` que llaman a la API real de FMP). Ningún test llama a internet.
- Linter: `ruff check .` (y `--fix`), formato: `ruff format .`. Config en `pyproject.toml`; excluye `learning/`.
- Instalar dependencias: `python -m pip install -r requirements.txt`.
- Ojo (Windows PowerShell 5.1): no reescribir archivos UTF-8 con `Get-Content`/`Set-Content`, corrompe las tildes. Usar las herramientas de edición o Python.

## Estado (revisado el 11-10-2026 ejecutando) — CHECKPOINT 1
- Confirmado: `python main.py` funciona de punta a punta para AAPL, MSFT y KO (5 años cada una): API -> DataFrame -> trazabilidad -> validación -> DuckDB (acumulando) -> lectura -> unión balance+resultados -> 10 ratios.
- Confirmado (16-10-2026): flujos de caja añadidos; `python main.py` OK con 9 llamadas; `pytest` pasa 59/59 y `ruff check .` limpio.
- Confirmado (20-10-2026): perfil de empresa + PER añadidos; `python main.py` OK con 12 llamadas; `pytest` 67/67; ruff limpio; las 4 páginas web dan 200.
- Confirmado (22-10-2026): 12 empresas (AAPL, MSFT, NVDA, GOOGL, AMZN, KO, PEP, WMT, JNJ, XOM, GE, PFE) OK con `python main.py` (48 llamadas); `pytest` 71/71; ruff limpio. `main.py` sigue con las demás si una empresa falla y lo resume al final. De pago en el plan FMP (402): PG, CAT, NEE, MCD, HON, UPS, LLY y eléctricas (DUK, SO, AEP, EXC, D).
- Confirmado (03-11-2026): página `/comparar/` (último ejercicio de cada empresa, sector, PER y 12 ratios, ordenada por sector; `pipeline.obtener_comparacion`, reutiliza `obtener_ratios` + `obtener_perfil`, ~1,3 s con 12 empresas). `pytest` 74/74; ruff limpio. Guía de estudio actualizada con lo del 22-10 y 03-11.
- CAMBIO DE FUENTE (03-11-2026, decisión 4 en `docs/decisiones.md`): `fmp_client.py` eliminado. `sec_client.py` traduce XBRL us-gaap (companyfacts) a los nombres camelCase de FMP con `ETIQUETAS` (lista de etiquetas por partida, vale la primera con dato cada año), solo 10-K, duración ~1 año, la presentación más reciente; deuda = no corriente + corriente (o suma de piezas); bruto = presentado o ventas - coste; capex = -pagos; cifras en float (si no, DuckDB devuelve huecos como <NA> y rompe `math.isnan`); ejercicio = año de (cierre - 7 días); `CIKS_MANUALES` = {XOM: 34088} (la holding nueva de Exxon aún no tiene 10-K). `yahoo_client.get_profile` (yfinance 1.7.0) sin logo. Validador: balance = identidad activo = pasivo + patrimonio (`total_liabilities_and_total_equity`), sin cuadre de FCF. Fuentes: `FUENTE = "SEC EDGAR (10-K)"`, `FUENTE_COTIZACION = "Yahoo Finance"`. Huecos esperados: margen operativo de JNJ/XOM/GE/PFE, bruto de XOM/GE, prueba ácida de GOOGL. Deuda sin arrendamientos operativos (AMZN baja de 18,7 % a 8,4 %). Confirmado: `main.py` OK con las 12 (unos 13 s), `pytest` 82/82, ruff limpio, 14 páginas web 200. Chequeo de eficiencia (03-11-2026): `obtener_comparacion` lee la base 2 veces en vez de 25 (0,44 s -> 0,07 s, mismos PER) y no falla si Yahoo no da el sector; el precio pasa por `_formatear`.
- (Histórico) Calidad de datos (03-11-2026): AAPL FY2026 (cierre 26-09-2026) llega de FMP con `total_debt` 2,0 mil M y `long_term_debt` 0 (en 2025: 112,4 y 78,3) -> deuda/activos 0,5 %. Casi seguro dato incompleto en FMP; el validador no lo detecta porque es coherente (net_debt = total_debt - cash). Resuelto al pasar a la SEC: sin 10-K presentado, la SEC no tiene ese año.
- (Histórico) `fmp_client.py` nunca relanza errores de `requests` (su mensaje lleva la URL con la clave): los cambia por `RuntimeError` propios sin URL (`from None`). Tests en `tests/test_fmp_client.py`.
- Arquitectura actual: `main.py` solo elige empresas y muestra; `src/pipeline.py` orquesta (`actualizar_empresa`, `obtener_ratios`); Django llamará a `src/pipeline.py` en el futuro.
- (Histórico, ya no existe) `fmp_client.py`: `get_balance_sheet`, `get_income_statement`, `get_cash_flow_statement`, `get_profile` (comparten `_get_estado_financiero`). Plan FMP de Carlos: `profile` y `quote` OK; `news/stock` y `sp500-constituent` dan 402 (de pago).
- `transformer.py`: `estado_a_dataframe` (antes `balance_sheet_a_dataframe`), `añadir_trazabilidad` (solo convierte `date` si existe: el perfil no la trae). (`unir_estados` en pandas se eliminó: la unión ahora es SQL.)
- `validator.py`: `validar_balance`, `validar_cuenta_resultados`, `validar_flujos_caja`, `validar_perfil` (1 fila, `market_cap` > 0) (comparten `_validar_comun`; `_comprobar_cuadre` verifica activo = pasivo + patrimonio (antes: deuda neta y FCF de FMP); el capex debe llegar en negativo).
- `duckdb_manager.py`: `guardar_estado(df, tabla)` borra e inserta solo las (symbol, date) que trae, en transacción; `obtener_estado(tabla, symbols)`. Tablas permitidas: `balance_sheet`, `income_statement`, `cash_flow_statement`, `company_profile` (date = día de descarga: una foto por día, acumula histórico). `obtener_datos_analisis(symbols)`: INNER JOIN de los 3 estados por symbol+date con columnas explícitas (`b.inventory` = saldo del balance) y error si salen periodos duplicados.
- Reparto acordado con Carlos: SQL para los datos (guardar, filtrar, unir); Python para fórmulas, limpieza y validación.
- Ratios: deuda/activos, deuda/patrimonio, liquidez corriente, prueba ácida, ratio de caja, márgenes bruto/operativo/neto, ROA, ROE, flujo de caja libre (OCF + capex, calculado por nosotros), margen FCF, calidad del beneficio (OCF / beneficio neto; NaN si beneficio <= 0). ROA/ROE con balance de cierre (no media). PER = capitalización actual / beneficio neto del último ejercicio (`calcular_per`, escalares; NaN si beneficio <= 0), lo da `pipeline.obtener_perfil`.
- Política de ratios: denominador 0 o nulo -> NaN (`_dividir`). Con patrimonio <= 0 también NaN (`_dividir_si_positivo`, para deuda/patrimonio y ROE).
- FMP da `interest_expense = 0` para AAPL: no fiarse de ese campo (por eso no hay cobertura de intereses).
- `*.duckdb` en `.gitignore`: la base se regenera con `python main.py` y no se sube.
- `docs/decisiones.md`: registro de decisiones (LLM no calcula; SQL datos / Python fórmulas; Django lee del motor, sin ORM para datos financieros).
- Django 6.1.2 (fase 2 iniciada 16-10-2026): `config/` (settings lee `DJANGO_SECRET_KEY` de `.env`; `RUTA_DUCKDB`), app `web/` con `inicio` (`/`, lista empresas) y `empresa` (`/empresa/<symbol>/`, tabla de ratios). Las vistas solo llaman a `src/pipeline.py` (`listar_empresas`, `obtener_ratios`, `obtener_perfil`) y solo formatean (%, coma decimal). Nombres de ratios en `NOMBRES_RATIOS` (`ratios.py`), compartidos con `main.py`. Tests de la web en `tests/test_web.py` (pytest-django, fixture `settings`); datos falsos de FMP en `tests/conftest.py`.
- Web local: `python manage.py runserver`. No ejecutar `main.py` con la web abierta (bloqueo de DuckDB).
- Carpeta de trabajo en este ordenador: `Desktop\AI FINANCIAL ANALYST`.

## Siguiente paso
0. AL EMPEZAR (cuando Carlos diga "empecemos"), sin pedirle que haga nada a mano (lo pidió el 03-11-2026):
   1. Ejecutar `.\inicio.ps1` (pull + dependencias, instala `yfinance` + tests). Si los tests no arrancan por `.env`, ver el punto 2 y repetir.
   2. Comprobar SIN leer ni imprimir `.env` (p. ej. `python -c "from dotenv import dotenv_values; print('SEC_USER_AGENT' in dotenv_values('.env'), 'DJANGO_SECRET_KEY' in dotenv_values('.env'))"`). Si falta `SEC_USER_AGENT`, añadir al final: `SEC_USER_AGENT=Carlos Bárcena Aguilar carlosbarcenaaguilar@gmail.com` (Carlos dio permiso). Si falta `DJANGO_SECRET_KEY`, generar una nueva y añadirla. La `API_KEY` de FMP ya no se usa.
   2b. Si falta `GEMINI_API_KEY`: es lo ÚNICO que Carlos tiene que poner a mano (una clave no viaja por git). Pedirle que la pegue en `.env` (la misma de este ordenador o una nueva de aistudio.google.com). Sin ella todo funciona salvo el botón de IA, que lo avisa.
   3. Si la base `ai_financial_analyst.duckdb` es anterior al cambio de fuente (su columna `fuente` en `balance_sheet` no es "SEC EDGAR (10-K)", o no existe la base), borrarla y ejecutar `python main.py` (debe terminar en "Pipeline completado correctamente").
   4. Contarle a Carlos en 2-3 líneas qué se ha hecho.
1. (19-10-2026) Carlos NO quiere avanzar hasta entender todo el código. Está estudiando con la "Guía de estudio del AI Financial Analyst" (Claude Doc, archivo por archivo y bloque a bloque): https://claude.ai/code/artifact/77b85f5f-732c-4545-bb96-3da49f64569d. Si cambia el código, actualizar la guía. Resolver sus dudas sobre ella antes de nada nuevo.
2. (20-10-2026) Carlos eligió: primero un analista SIN IA completo, luego la IA (no tiene aún clave de Anthropic). Plan acordado (S&P 500 entero descartado: noticias/lista de pago y límite de llamadas): 1) ~~perfil + cotización + PER en la página de empresa, enlace a noticias de Yahoo~~ hecho; 2) ~~más empresas~~ hecho (12, sin bancos ni eléctricas); 3) ~~página de comparación~~ hecho; 4) ~~IA~~ hecha (Gemini). Siguiente propuesto: verificador automático de que cada número de la explicación está en la ficha.
3. Objetivo general: prototipo para enseñar al profesor del TFG con el MÍNIMO código nuevo posible (bonito y fácil, sin abrumar). Web ya con Pico.css (CDN, versión classless en `base.html`; sin internet sale sin estilo). Ideas solo si hacen falta para la demo: comparar empresas, mostrar estados financieros, botón de actualizar (cuidado con el bloqueo de DuckDB).
- Cada ordenador necesita `DJANGO_SECRET_KEY` en su `.env` (si falta, pytest ni arranca). Tras un pull con estados nuevos, regenerar la base con `python main.py`.

- CAPA IA (03-11-2026, decisión 5): `src/formato.py` (`formatear`, `RATIOS_EN_PORCENTAJE`, movidos desde views.py: web e IA usan el mismo formato); `src/llm/explicador.py` (`explicar(ficha)` -> (texto, modelo); `MODELOS` = flash-lite primero y 3.8-flash de reserva; 503/429/timeout -> siguiente; `ESPERA_MAXIMA` 20 s; error propio si todos fallan); `pipeline.ficha_empresa` (texto con todas las cifras formateadas) y `pipeline.explicar_empresa`; web: botón "Explicar con IA" (`?explicar=1`) en empresa.html, la vista captura RuntimeError y la página sigue. Confirmado: explicaciones reales de AAPL/XOM/KO en 2-3 s, ningún número fuera de la ficha; `pytest` 94/94; ruff limpio.

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
