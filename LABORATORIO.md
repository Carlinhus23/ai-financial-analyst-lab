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

Guía: tabla de mejoras `mrvek3gz8sk.7238` (cambia de id si se reescribe).
Para añadir una fila, LEER antes la tabla (`view` + `parentId`): si Carlos ha
cambiado alguna Decisión, conservarla (mismo `index` en su dropdown). Secciones
`### N.` al final de la pestaña (insert en root, end). Última rev: 4.
