# Bitácora de uso de IA

Proyecto: Agente de WhatsApp y catálogo web para Urban (SeminarioIA_Alexyulian21)
Estudiante: Alex Yulian Caviedes Córdoba
Funcionalidad: HU-01 Consultar si una prenda está disponible en mi talla y cuánto vale (`buscar_prenda`)
Asistente usado: Claude en chat (contrato y pruebas) y Claude Code en VS Code, modo agente con aprobación **Manual** de cada edición (implementación y refactor)

## Entradas

### Entrada 1

- **Fecha:** 2026-11-07
- **Prompt o sugerencia:** Le pedí a Claude un borrador del contrato de HU-01 para el README a partir de mi documento de requisitos de la semana 3 y del diseño de la semana 4. Propuso `buscar_prenda(catalogo, reservas_activas, codigo, color, talla)` con ejemplos inventados (`po-01`).
- **Decisión:** Aceptada con cambios
- **Por qué:** Al revisarlo contra mi catálogo real (`productos.js`) vi que no hay campo de color (cada código ya es un color), que el precio 0 significa «Consultar precio» y que las gorras son talla única. Quité el parámetro `color`, agregué `precio = None` cuando es 0, la talla «UNICA» y usé códigos reales (th-01, je-01, bu-01, go-01).
- **Verificación:** Comparé cada campo del contrato con `productos.js` y con la HU-01 y sus criterios CA-01.1 y CA-01.2 del documento de la semana 3.
- **Commit relacionado:** `56c4cae` Contrato completo de HU-01 en el README

### Entrada 2

- **Fecha:** 2026-11-07
- **Prompt o sugerencia:** La IA me indicó subir los cambios con `git push origin principal`, porque GitHub mostraba la rama como «principal».
- **Decisión:** Aceptada con cambios
- **Por qué:** El push no subió nada. `git status` mostró `On branch main`: GitHub en español traduce el nombre, pero la rama real es `main`. Cambié el comando a `git push origin main`.
- **Verificación:** `git log --oneline` mostró `(HEAD -> main, origin/main)` en el commit del contrato.
- **Commit relacionado:** `d825a7c` Contrato de HU-01 (buscar_prenda) en el README y .gitignore

### Entrada 3

- **Fecha:** 2026-11-07
- **Prompt o sugerencia:** Le pedí a Claude las pruebas a partir de la tabla de ejemplos del contrato. Propuso 10 pruebas pytest (2 normales, 5 de límite y 3 de error) y un esqueleto de `buscar_prenda` que solo lanza `NotImplementedError`.
- **Decisión:** Aceptada
- **Por qué:** Cada prueba corresponde a una fila de la tabla de ejemplos o a un caso límite del contrato (todo reservado, `disponible = NO`, más reservas que cantidad, precio 0, no modificar las listas). El caso de error cubre CA-01.2. El esqueleto hace que fallen por la razón correcta y no por un error de importación.
- **Verificación:** Leí cada prueba contra la tabla del README y corrí `python -m pytest`: **10 failed** con `NotImplementedError`.
- **Commit relacionado:** `cb2bb1c` Pruebas de buscar_prenda (en rojo)

### Entrada 4

- **Fecha:** 2026-11-07
- **Prompt o sugerencia:** Prompt a Claude Code con rol, contexto (`@README.md @app/buscar_prenda.py @tests/test_buscar_prenda.py`), tarea, formato y restricciones: «implementa buscar_prenda para que pasen las 10 pruebas; solo librería estándar; no modifiques ni borres las pruebas; no hagas commits». Cambié el modo de «Auto» a «Manual» para aprobar cada edición.
- **Decisión:** Aceptada
- **Por qué:** Solo editó `app/buscar_prenda.py`, mantuvo la firma y `PrendaNoEncontrada`, no agregó librerías y listó sus supuestos (comparación exacta, solo «SI» cuenta como disponible, `max(..., 0)` para no dar negativo). Puedo explicar cada línea.
- **Verificación:** Corrí `python -m pytest` en mi terminal: **10 passed in 0.13s**.
- **Commit relacionado:** `9a07423` Implementación de buscar_prenda con el asistente (pruebas en verde)

### Entrada 5

- **Fecha:** 2026-11-07
- **Prompt o sugerencia:** Pedí a Claude Code que propusiera refactors sin editar. Propuesta 1: constantes `DISPONIBLE = "SI"` y `PRECIO_A_CONSULTAR = 0`.
- **Decisión:** Aceptada con cambios
- **Por qué:** Acepté `DISPONIBLE` porque quita el valor mágico `"SI"`, pero no `PRECIO_A_CONSULTAR`: al rechazar la propuesta 4 (entrada 7) esa constante quedaba sin usar.
- **Verificación:** `python -m pytest`: 10 passed, sin tocar las pruebas.
- **Commit relacionado:** `d48518b` Refactor de buscar_prenda

### Entrada 6

- **Fecha:** 2026-11-07
- **Prompt o sugerencia:** Propuestas 2, 3 y 5 del refactor: renombrar `f` y `r` por `fila_catalogo` y `reserva`, separar la suma en `_unidades_reservadas(reservas_activas, codigo, talla) -> int` y usar una cláusula de guarda para `disponible`.
- **Decisión:** Aceptada
- **Por qué:** Son cambios de estructura que no cambian el comportamiento: nombres más claros, la función principal queda en buscar la fila, calcular las libres y armar la respuesta, y se quita el `if/else` anidado.
- **Verificación:** `python -m pytest`: 10 passed. `git diff --stat` mostró que solo cambió `app/buscar_prenda.py`.
- **Commit relacionado:** `d48518b` Refactor de buscar_prenda

### Entrada 7

- **Fecha:** 2026-11-07
- **Prompt o sugerencia:** Propuesta 4 del refactor: cambiar `fila["precio"] or None` por `None if fila["precio"] == PRECIO_A_CONSULTAR else fila["precio"]`.
- **Decisión:** Rechazada
- **Por qué:** El mismo asistente avisó que cambia el comportamiento con una celda vacía de la hoja: hoy `""` da `None` y con el cambio devolvería `""`. Un refactor no debe cambiar el comportamiento observable. Dejé `or None` con el comentario «Precio 0 significa «Consultar precio»: se devuelve None».
- **Verificación:** Revisé el caso `""` a mano y las 10 pruebas siguieron pasando con el código sin ese cambio.
- **Commit relacionado:** `d48518b` Refactor de buscar_prenda

### Entrada 8

- **Fecha:** 2026-11-07
- **Prompt o sugerencia:** El asistente señaló posibles cambios de regla de negocio: aceptar «si», « SI» o espacios en `disponible`, `codigo` y `talla`; rechazar precios o cantidades negativas; avisar si hay filas duplicadas.
- **Decisión:** Rechazada (por ahora)
- **Por qué:** Cambian el contrato de HU-01, no son refactors. Los dejo como pendientes, en especial los espacios de más que pueden venir de Google Sheets, que harían que una prenda salga como agotada o no encontrada.
- **Verificación:** El contrato del README dice que la comparación es exacta; ninguna prueba cubre esos casos todavía.
- **Commit relacionado:** No aplica (pendiente para una próxima historia)

## Resumen

| Decisión | Cantidad |
|---|---|
| Aceptadas | 3 |
| Aceptadas con cambios | 3 |
| Rechazadas | 2 |

## Errores que atraparon las pruebas

Con el esqueleto, las 10 pruebas fallaron con `NotImplementedError`, lo que confirmó que fallaban por la razón correcta antes de pedir el código. El código que generó el asistente pasó las 10 pruebas en el primer intento, así que ninguna prueba falló con él. Lo más importante salió en el refactor: la propuesta 4 cambiaba el resultado para una celda de precio vacía (`""`) y **ninguna de mis pruebas lo habría detectado**, porque no tengo una prueba con precio vacío. Lo atrapó la revisión, no las pruebas. La próxima vez agregaría una prueba de caracterización para ese caso antes de refactorizar.

## Reflexión final (5 a 8 líneas)

El asistente me ayudó más a convertir el contrato en pruebas concretas y a escribir la implementación rápido, en un solo intento.
Lo que más aprendí fue a no aceptar todo: el primer contrato tenía un parámetro `color` que mi catálogo real no tiene, y una instrucción de git usaba una rama que no existía.
Usar el modo Manual de Claude Code me obligó a leer cada cambio antes de aceptarlo.
En el refactor vi la diferencia entre mejorar la estructura y cambiar el comportamiento: rechacé un cambio que parecía inofensivo porque alteraba el caso de una celda vacía.
Las pruebas pasaron siempre, pero eso me mostró que solo protegen lo que cubren.
En la próxima funcionalidad escribiría primero las pruebas de datos raros de la hoja (vacíos, espacios, mayúsculas) y revisaría el contrato contra los datos reales antes de pedir código.
