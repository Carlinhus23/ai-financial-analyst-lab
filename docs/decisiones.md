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
