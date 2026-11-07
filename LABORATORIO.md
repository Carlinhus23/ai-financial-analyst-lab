# Laboratorio: reglas del loop

Pedido por Carlos el 07-11-2026. Cuando diga "empieza el loop", se programa una
tarea cada 5 minutos (`CronCreate`, `*/5 * * * *`) con el texto:
"Vuelta del loop del laboratorio: sigue LABORATORIO.md". Cuando diga "termina el
loop" (o "para"), se borra con `CronDelete`. Las tareas solo viven mientras dure
la sesión de Claude Code y caducan a los 7 días.

## Cada vuelta (UNA sola mejora, nunca dos)

1. Si la vuelta anterior no ha terminado, no empezar otra.
2. `git pull` en esta carpeta. Comprobar que `pytest` pasa antes de tocar nada.
3. Elegir la primera idea de la cola que no esté hecha. Si una idea pide una
   dependencia nueva, mover archivos o cambiar la arquitectura, saltarla y
   dejarla anotada para preguntar a Carlos.
4. Hacerla con el MÍNIMO código, siguiendo `CLAUDE.md` (el LLM no calcula,
   `src/` no importa Django, tests sin internet, nunca leer `.env`).
5. Tests nuevos para lo nuevo. `pytest` y `ruff check .` limpios. Si algo
   falla y no se arregla en esa vuelta: `git restore .` y anotar el motivo.
6. `.\fin.ps1 "<mensaje en inglés>"`: un commit por mejora, subido al lab.
7. Guía de estudio, pestaña "Laboratorio (mejoras propuestas)": añadir una fila
   a la tabla de mejoras y una sección `### N. <nombre>` al final con:
   qué hace · por qué te conviene (venderla, para la demo y el TFG) ·
   dificultad para Carlos (x/5 y por qué, según la escala de la pestaña) ·
   archivos tocados · cómo verlo · commit (para `git cherry-pick`) ·
   de qué mejoras anteriores depende.
8. Mover la idea a "Hechas" abajo, con el hash del commit.
9. Contar a Carlos en 3-4 líneas qué se ha hecho y la frase de venta.

## Pasar una mejora al principal (solo si Carlos lo pide)

En la carpeta principal: `git fetch lab` (remoto
`https://github.com/Carlinhus23/ai-financial-analyst-lab.git`; añadirlo si
falta) y `git cherry-pick <hash>`. Luego tests, ruff, actualizar las DOS
pestañas de la guía y poner la decisión "Ya en el principal".

## Ids de la guía de estudio

- Doc: `77b85f5f-732c-4545-bb96-3da49f64569d`
- Pestaña Laboratorio: archivo `8489c591-5a02`, cuerpo `beca36f9-3a67`
- Enum "Decisión": `d9c92ff1-995e` (0 Pendiente de decidir, 1 Pasar al
  principal, 2 Descartar, 3 Ya en el principal)
- Leer con `sinceRev` antes de editar: Carlos puede haber cambiado la tabla.

## Cola de interfaz (PRIORIDAD: Carlos pidió "mejora la interfaz", 07-11-2026)

Sin dependencias nuevas: Pico.css (ya está) + CSS propio en `base.html`.
Nada de colores que juzguen "bueno/malo" un ratio (depende del sector).

I1. Portada con tarjetas por empresa (nombre, precio, PER, crecimiento de
    ventas), agrupadas por sector.
I2. Tabla de ratios de la empresa agrupada en bloques (endeudamiento y
    liquidez, rentabilidad, eficiencia, caja, crecimiento).
I3. Fórmula de cada ratio al pasar el ratón por su nombre.
I4. Cabecera de empresa con cifras destacadas grandes (precio,
    capitalización, PER).
I5. Verde/rojo solo para el SIGNO de variaciones (sesión, crecimiento).
I6. Comparar: cabecera y primera columna fijas al desplazarse.
I7. Botón "Explicar con IA" con indicador de espera (aria-busy de Pico).
I8. Navegación: página actual marcada y selector rápido de empresa.

## Cola de ideas (por orden; las primeras, las más vistosas para la demo)

1. Verificador de cifras de la IA: avisar si la explicación trae un número
   que no está en la ficha.
2. Crecimiento interanual de ventas y beneficio neto en la página de empresa.
3. Gráfico de la evolución de los ratios en la página de empresa (Chart.js por
   CDN, como Pico.css).
4. Mostrar los estados financieros (balance, resultados y flujos) de la empresa.
5. Mediana del sector en `/comparar/` (contexto sin umbrales arbitrarios).
6. Enlace a cada 10-K original en la SEC (trazabilidad de la fuente).
7. Ordenar la tabla de `/comparar/` pulsando en la cabecera.
8. Descargar los ratios de una empresa en CSV.
9. Rotación de activos y días de inventario (ratios nuevos con tests).
10. Guardar la última explicación de la IA para no repetir la llamada.
11. Cobertura de intereses con `InterestExpense` de la SEC (si hay dato fiable).
12. Explicación de la IA comparando dos empresas.

## Hechas

- Idea 1 · Verificador de cifras de la IA · `76bf119` · 2/5 (07-11-2026).
- Idea 2 · Crecimiento interanual de ventas y beneficio · `ac59c3d` · 2/5
  (07-11-2026).
- Idea 3 · Minigráficos SVG de evolución (sin Chart.js: sería dependencia
  nueva; si Carlos quiere gráficos grandes, preguntarle) · `2531b5d` · 3/5
  (07-11-2026).
- Idea 4 · Estados financieros (desplegable, millones) · `a61ac9e` · 1/5
  (07-11-2026).
- Idea 5 · Mediana del sector en Comparar · `090bf46` · 2/5 (07-11-2026).
- Idea 6 · Enlace a la lista de 10-K de la empresa en la SEC · `da222e5` · 1/5
  (07-11-2026). Pendiente (preguntar a Carlos): enlace al 10-K de cada año,
  guardando el `accn` en una columna nueva (hay que regenerar la base).

- Idea 7 · Ordenar Comparar por un ratio, dentro de cada sector · `b257cd6` ·
  2/5 (07-11-2026). Depende de la 5.

- Idea 8 · Descargar los ratios en CSV para Excel · `9f94319` · 2/5
  (07-11-2026).

- Idea 9 · Rotación de activos y días de inventario · `c1bb35f` · 1/5
  (07-11-2026).

- Idea 10 · Guardar explicaciones de la IA en DuckDB (tabla ai_explanation,
  clave = ficha exacta) · `754aab2` · 3/5 (07-11-2026). Depende de la 1.
  Posible mejora: botón "pedir otra explicación".

- I1 · Portada con tarjetas (guía: mejora 11) · `fef633e` · 2/5 (07-11-2026).
  Depende de la 2.
- I2 · Ratios agrupados en bloques (guía: mejora 12, `GRUPOS_RATIOS`) ·
  `1c0e5cf` · 1/5 (07-11-2026). Depende de 2, 3 y 9.
- I3 · Fórmula al pasar el ratón (guía: mejora 13, `FORMULAS_RATIOS`) ·
  `3d9b5eb` · 1/5 (07-11-2026). Depende de la 12.
- I4 · Precio, capitalización y PER en grande (guía: mejora 14) · `959d2c6` ·
  1/5 (07-11-2026).
- I5 · Verde/rojo solo para variaciones (guía: mejora 15,
  `COLUMNAS_CON_SIGNO`) · `765ba58` · 2/5 (07-11-2026). Depende de 2, 11, 12, 14.

Loop cada 3 min (Carlos, 07-11-2026), prioridad a la interfaz. Siguiente: I6.
En mejoras visuales, MIRARLAS: reiniciar la web (con --noreload no recarga
plantillas) y captura con Edge sin ventana:
`msedge --headless=new --disable-gpu --hide-scrollbars --window-size=1280,1000
--screenshot=<scratchpad>\x.png http://127.0.0.1:8001/...`, luego leer la imagen.
Web del lab para Carlos: `runserver 8001 --noreload` en segundo plano (el
recargador automático no detectó cambios): reiniciarla tras cada mejora.

Guía: tabla de mejoras `mrvek3gz8sk.44760` (cambia de id si se reescribe).
Ejemplos con cifras en la guía: sacarlas SIEMPRE de los datos reales.
Para añadir una fila, LEER antes la tabla (`view` + `parentId`): si Carlos ha
cambiado alguna Decisión, conservarla (mismo `index` en su dropdown). Secciones
`### N.` al final de la pestaña (insert en root, end). Última rev: 22.
