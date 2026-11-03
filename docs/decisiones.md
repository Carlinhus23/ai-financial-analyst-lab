# Registro de decisiones

Decisiones de diseño del proyecto, con su motivo. Se añaden al final, con fecha.

## 1. El LLM nunca calcula cifras (desde el inicio)

**Decisión:** todas las cifras y ratios se calculan con código determinista
(Python/pandas) y con tests. El LLM solo interpretará métricas ya calculadas.

**Motivo:** un LLM puede equivocarse en aritmética o inventar datos; en un
análisis financiero eso invalida el resultado. El código con tests es
reproducible y auditable.

## 2. SQL para los datos, Python para las fórmulas (16-10-2026)

**Decisión:** DuckDB (SQL) guarda, filtra y une los tres estados financieros
(`obtener_datos_analisis`, un `INNER JOIN` por empresa y fecha). Las fórmulas de
los ratios, la limpieza y la validación se quedan en Python.

**Motivo:**
- Unir tablas es la tarea para la que existe SQL. Escribir `b.inventory` deja
  claro de qué estado sale cada columna; con la unión anterior en pandas, la
  columna repetida dependía del orden de unión (el flujo de caja también tiene
  `inventory`, pero es la variación del año, no el saldo).
- La consulta solo trae las columnas que usan los ratios: documenta qué datos
  intervienen en el análisis.
- Cada fórmula en Python se prueba con una tabla de 2-3 filas, sin base de
  datos. En SQL cada test necesitaría montar una base.

**Alternativa descartada:** calcular los ratios en SQL (vistas). Válido, pero
peor para probar fórmula a fórmula y contrario a la decisión 1.

## 3. Django lee del motor; los datos financieros no pasan al ORM (16-10-2026)

**Decisión:** la web (Django, carpetas `config/` y `web/`) obtiene los datos
llamando a `src/pipeline.py` (`listar_empresas`, `obtener_ratios`). Los datos
financieros siguen en DuckDB. La base de Django (SQLite, `db.sqlite3`) solo
guarda lo interno de Django (administración, sesiones).

**Motivo:**
- `src/` sigue siendo Python puro y se prueba sin web.
- No se reescribe ni se duplica el guardado que ya funciona y está probado.
- La web es sustituible: otra interfaz podría llamar al mismo motor.

**Alternativa descartada:** modelos `Company`, `Statement` y `Ratio` en el ORM de
Django. Daría el panel de administración gratis, pero obligaría a duplicar o
reescribir la persistencia y haría depender el motor de Django.

**Límite conocido:** DuckDB no permite que un proceso escriba mientras otro
tiene el archivo abierto. No conviene ejecutar `python main.py` con la web
encendida. Si llega a ser un problema, se revisará esta decisión.

## 4. Estados financieros de la SEC y cotización de Yahoo, en lugar de FMP (03-11-2026)

**Decisión:** los estados financieros salen de SEC EDGAR (cuentas anuales 10-K,
`src/data/sec_client.py`) y el perfil con la cotización (precio, capitalización,
sector) de Yahoo Finance (librería `yfinance`, `src/data/yahoo_client.py`).
Ambos devuelven los datos con los nombres que usaba FMP, así que el resto del
motor no cambia.

**Motivo:**
- El plan gratuito de FMP se quedaba corto: unas 250 llamadas al día, noticias y
  lista del S&P 500 de pago, y empresas como PG, CAT, LLY o las eléctricas de pago.
- La SEC es la fuente oficial: son las cifras que la empresa presenta ante el
  regulador. Gratis, sin clave y para todas las empresas que cotizan en EE. UU.
- FMP dio para Apple un ejercicio 2026 con la deuda casi a cero antes de que
  Apple presentara su 10-K: probablemente salía de resultados preliminares. La
  SEC solo tiene cuentas presentadas.

**Cómo se traduce la SEC:** cada empresa etiqueta sus partidas a su manera
(XBRL us-gaap). Cada partida tiene una lista de etiquetas por orden de
preferencia y, cada año, vale la primera que tenga dato. Dos partidas se
construyen:
- Deuda financiera = deuda no corriente + deuda corriente. Si la empresa no da
  la deuda corriente total, se suman sus piezas (deuda a largo que vence en el
  año, pagarés y préstamos a corto). Sin arrendamientos operativos; en KO, XOM y
  GE la deuda no corriente incluye arrendamientos financieros.
- Beneficio bruto = el presentado o, si no, ventas - coste de ventas.

**Límites conocidos:**
- Muchas empresas no presentan resultado operativo (J&J, Exxon, GE, Pfizer) ni
  beneficio bruto o coste de ventas (Exxon, GE): esos ratios salen "—". La SEC
  no estandariza; los proveedores comerciales rellenan esos huecos con criterios
  propios.
- La validación del balance pasa de "deuda neta de FMP = deuda - caja" a la
  identidad contable activo = pasivo + patrimonio. Ya no se contrasta el FCF con
  la fuente: la SEC no lo da y lo calculamos nosotros.
- yfinance no es un servicio oficial: Yahoo puede cambiarlo o bloquearlo. Por
  eso solo se usa para la cotización, y sus fallos dan un error propio.
- La SEC exige identificarse con nombre y email (`SEC_USER_AGENT` en `.env`).

**Alternativas descartadas:** yfinance para todo (datos ya estandarizados, pero
no oficiales y solo 4 años) y seguir con FMP (límites del plan gratuito).

## 5. Capa de IA con la API gratuita de Gemini (03-11-2026)

**Decisión:** el LLM es Gemini, con el plan gratuito de su API
(`src/llm/explicador.py`). Recibe solo la "ficha" de la empresa
(`pipeline.ficha_empresa`): sus ratios ya calculados, escritos con el mismo
formato que la web (`src/formato.py`). Se pide desde la web con el botón
"Explicar con IA" (no al cargar la página).

**Motivo:**
- Gratis. La suscripción Google AI Pro de estudiante no incluye la API, pero la
  API tiene plan gratuito para los modelos Flash.
- Funciona en cualquier ordenador con internet (un modelo local con Ollama
  exigía un ordenador potente).
- Cumple la decisión 1: el LLM no recibe datos en bruto ni calcula; solo
  explica cifras que ya se ven en la web.

**Comprobado (03-11-2026):** en las explicaciones de AAPL, XOM y KO, todos los
números que escribe el LLM (entre 21 y 36 por explicación) están en la ficha:
no inventó ninguno.

**Límites conocidos:**
- En el plan gratuito, Google usa el contenido enviado para mejorar sus
  productos. Solo se envían ratios públicos de empresas cotizadas.
- Los modelos se saturan a menudo (error 503). Se prueban por orden
  (`MODELOS`: Flash-Lite primero, que responde en 2-3 s) y cada uno espera como
  mucho 20 s. Si todos fallan, la web lo dice y sigue funcionando.
- La explicación puede interpretar mal una cifra: la web lo avisa.

**Alternativas descartadas:** Claude (API de pago), un modelo local con Ollama
(el otro ordenador de Carlos no puede con él).
