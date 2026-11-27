# Bitácora de uso de IA

Proyecto: Agente de WhatsApp y catálogo web para Urban (SeminarioIA_Alexyulian21)
Estudiante: Alex Yulian Caviedes Córdoba
Funcionalidad: HU-01 Consultar si una prenda está disponible en mi talla y cuánto vale (`buscar_prenda`)
Semana 6: revisión y seguridad
Semana 7: pruebas con IA de las reglas de reservas (`app/reservas.py`)
Asistente usado: Claude en chat (contrato y pruebas) y Claude Code en VS Code, modo agente con aprobación **Manual** de cada edición (implementación y refactor). En la semana 7, Claude en la nube trabajó en la rama `semana7-pruebas` a partir de mis reglas y decisiones, y yo revisé y confirmé cada decisión antes del pull request.

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

### Entrada 9

- **Fecha:** 2026-11-14
- **Prompt o sugerencia:** Con Claude Code (Opus 5.5) en VS Code, en modo Manual y solo lectura, usé el prompt de revisión de la semana (Rol, Contexto, Tarea, Formato, Restricciones): revisar `app/buscar_prenda.py`, las pruebas y el README contra el OWASP Top 10 2021, sin modificar archivos ni ejecutar comandos. Propuso una tabla de hallazgos separada en problemas seguros y sospechas, y la tabla de los 5 puntos de seguridad (inyección, secretos, contraseñas, control de acceso y dependencias).
- **Decisión:** Aceptada
- **Por qué:** Clasifiqué como reales los 5 hallazgos seguros: falta la prueba de cantidad 0 (H-03), no se prueba la herencia de `LookupError` (H-04), `or None` deja la regla implícita (H-05), falta `requires-python` (H-07) y la trazabilidad del CA-01.1. No hubo falsos positivos. Las sospechas (datos de la hoja como texto, reservas negativas, filas duplicadas, log injection) no las cuento como reales hasta tener el lector de la hoja; quedaron como pendientes. Los demás hallazgos no salieron de la IA: H-01 y H-02 vienen del linter y de la configuración previa, H-06 lo encontré yo con la lista de revisión y H-08 lo pedí yo después.
- **Verificación:** Leí cada línea citada (por ejemplo `README.md:70` y `README.md:54`, sin prueba para esos límites), corrí pytest y ruff después de cada corrección y registré todo en `revision_seguridad.md`.
- **Commit relacionado:** `3899f6d`, `ff05753`, `54e6a07`, `09ca9b5` (correcciones) y `ffa707c` (informe)

### Entrada 10

- **Fecha:** 2026-11-14
- **Prompt o sugerencia:** Le pedí al agente de Claude Code crear la constante `PRECIO_CONSULTAR = 0` y cambiar `fila["precio"] or None` por una comparación explícita. Propuso `None if fila["precio"] == PRECIO_CONSULTAR else fila["precio"]` y lo subió en `ff05753` con el mensaje «Mismo comportamiento».
- **Decisión:** Aceptada con cambios
- **Por qué:** El mensaje era falso: con precio `""` el resultado pasó de `None` a `""`. Era el mismo cambio que yo había rechazado en la entrada 7. Ni el agente ni yo lo vimos al revisar el diff. Lo detectó Claude Code al leer esta bitácora para escribir el README. De las tres opciones que propuso (revertir, documentar o tratar `""` también como «Consultar precio»), elegí la tercera: conserva la constante y vuelve al comportamiento anterior. No reescribí el historial; el commit de la corrección cita a `ff05753`.
- **Verificación:** Escribí primero `test_precio_vacio_devuelve_none` y la vi fallar (`assert '' is None`, 1 failed, 12 passed). Después cambié la comparación a `fila["precio"] in (PRECIO_CONSULTAR, "")`: 13 passed y ruff sin avisos.
- **Commit relacionado:** `ff05753` (error), `ea6db49` (corrección) y `abedac2` (README e informe)

### Entrada 11

- **Fecha:** 2026-11-14
- **Prompt o sugerencia:** Le di a Claude Code una tarea de agente en la rama `agente/revision-semana6`, con un commit por punto y pytest y ruff después de cada uno. Le di permisos mínimos: solo tocar `app/`, `tests/` y `pyproject.toml`; no instalar paquetes, no leer `.env`, no hacer push ni merge, y detenerse a preguntar si tenía que cambiar una prueba existente. Hizo 6 commits.
- **Decisión:** Aceptada
- **Por qué:** Respetó las restricciones y solo agregó pruebas nuevas. Trabajar en una rama aparte me dejó revisar todo antes de que llegara a `main`. Por honestidad: la corrección del precio vacío (`ea6db49` y `abedac2`) no pasó por esa rama, la hice directo en `main`. También ahí revisé el diff antes de aprobar cada commit.
- **Verificación:** Revisé los cambios con `git diff main..agente/revision-semana6` y los integré con merge (fast-forward). Esa revisión no detectó el error de `ff05753` (entrada 10).
- **Commit relacionado:** `3899f6d`, `ff05753`, `4eb3a40`, `54e6a07`, `09ca9b5`, `99db1bb` (rama del agente); `ea6db49`, `abedac2` (directo en `main`)

### Entrada 12

- **Fecha:** 2026-11-14
- **Prompt o sugerencia:** Lección de la semana, a partir de las entradas 7 y 10.
- **Decisión:** No aplica (lección)
- **Por qué:** Que las pruebas sigan en verde no demuestra que el comportamiento no cambió si ninguna prueba cubre ese caso. `ff05753` pasó las 12 pruebas y aun así cambió el resultado para un precio vacío. En la entrada 7 ya había escrito que agregaría una prueba de caracterización antes de refactorizar, y no lo hice.
- **Verificación:** La prueba `test_precio_vacio_devuelve_none` falla con el código de `ff05753` y pasa con la corrección. Desde ahora, antes de un refactor escribo las pruebas de los casos que el cambio podría tocar (vacíos, espacios, mayúsculas) y no confío en un mensaje de «mismo comportamiento» sin una prueba que lo respalde.
- **Commit relacionado:** `ea6db49`

### Entrada 13

- **Fecha:** 2026-11-22
- **Prompt o sugerencia:** Prompt 1 de clase (rol: analista de pruebas; tarea: casos con particiones, límites y tabla de decisión, sin código; el esperado sale de la regla y se señala lo ambiguo) para las cuatro reglas de reservas. La primera propuesta de la IA tomaba «precio 0 o None» como el único precio inválido, no ponía máximo de unidades y dejaba como duda si a las 24 h exactas la reserva ya vence.
- **Decisión:** Aceptada con cambios
- **Por qué:** Contesté las ambigüedades con lo que pasa en la tienda: «si vence a las 24 horas»; el producto más barato vale 40.000 (una gorra), así que un precio menor es un error; «lo normal es 4 o 5» unidades por reserva, y se tomó 5 como máximo; y se pueden pedir «las que queden». Eso agregó los límites 39.999/40.000, cantidad 5/6 y libres = cantidad. «Nu Bank» y «Nequí» quedaron como ambigüedades abiertas.
- **Verificación:** Revisé la propuesta con las 5 preguntas de clase (particiones, límites, origen del esperado, ambigüedades y reglas inventadas). Cada fila de las tablas cita la regla de la sección 1 de `registro_pruebas.md`.
- **Commit relacionado:** `3116c1b` (reglas) y `1e4e546` (tablas de casos y tabla de decisión)

### Entrada 14

- **Fecha:** 2026-11-22
- **Prompt o sugerencia:** Prompt 2 de clase (rol: desarrollador que escribe pruebas con pytest; contexto: `app/reservas.py` y el registro; una fila de `parametrize` por caso, `pytest.raises(ValueError)`, esperados fijos, sin tocar `app/`). La IA generó `tests/test_reservas.py` con 47 pruebas.
- **Decisión:** Aceptada con cambios
- **Por qué:** Los esperados salían de la regla y usaba `is True`/`is False` y el tipo de error exacto, pero: los ids automáticos (`[creada_en0-ahora0-False]`) no dejaban saber qué caso cubría cada prueba; 3 líneas rompían ruff (E501); y en `puede_reservar` había filas redundantes. Rompí cada condición por separado y D4, D6, D7 y D8 nunca fallaron, así que las descarté. También uní R4-2 con D2 y R4-6 con D3. Quedaron 41 pruebas. Detalle en la sección 2 del registro.
- **Verificación:** `python -m pytest -q`: 47 passed antes y 41 passed después (54 con las de `buscar_prenda`). `ruff check .` limpio. `git diff 4200bbe dde0e18 -- tests/test_reservas.py` muestra la revisión.
- **Commit relacionado:** `4200bbe` (tal como la dio la IA) y `dde0e18` (revisión)

### Entrada 15

- **Fecha:** 2026-11-22
- **Prompt o sugerencia:** No es un prompt: rompí el código a propósito 5 veces, una a la vez, y deshice cada cambio con `git restore app/reservas.py`.
- **Decisión:** No aplica (verificación)
- **Por qué:** Cuatro cambios los detectó la suite (`<=` por `<`, `>=` por `>`, `*` por `+` y `<` por `<=` en el precio mínimo). El cambio `strip()` por `strip(" ")` **no lo detectó ninguna prueba**: todas pasaban con espacios, pero un mensaje de WhatsApp puede llegar con un salto de línea al final. Agregué el caso R2-13 `"nequi\n"` → `"nequi"`.
- **Verificación:** Con `strip(" ")`, R2-13 falla (1 failed, 54 passed); con el código bueno, 55 passed. Tabla en la sección 3 del registro.
- **Commit relacionado:** `7aa3828`

### Entrada 16

- **Fecha:** 2026-11-22
- **Prompt o sugerencia:** Prompt 3 de clase adaptado (rol: analista que prepara datos; tienda de ropa urban en Palermo; 15 reservas variadas y 5 casos difíciles; CSV; ninguna persona real; teléfonos 300 000 xxxx; sin la columna del esperado).
- **Decisión:** Aceptada con cambios
- **Por qué:** Dos nombres tenían apellidos del docente del seminario (Trujillo y Artunduaga): los cambié para que ningún dato se parezca a una persona conocida. La columna `forma_pago_esperada` la llené con la regla 2 y no la dejé a la IA, para que el oráculo siga siendo la regla.
- **Verificación:** Revisé que ningún nombre fuera de una persona real y que estuvieran los casos difíciles (tildes, ñ, apóstrofo, cliente vacío, salto de línea, forma de pago vacía). `test_datos_sinteticos_son_ficticios` comprueba las 20 filas y el patrón de teléfono. 57 passed.
- **Commit relacionado:** `f3212d9`

## Resumen

| Decisión | Cantidad |
|---|---|
| Aceptadas | 5 |
| Aceptadas con cambios | 7 |
| Rechazadas | 2 |
| No aplica (lección o verificación) | 2 |

## Errores que atraparon las pruebas

Con el esqueleto, las 10 pruebas fallaron con `NotImplementedError`, lo que confirmó que fallaban por la razón correcta antes de pedir el código. El código que generó el asistente pasó las 10 pruebas en el primer intento, así que ninguna prueba falló con él. Lo más importante salió en el refactor: la propuesta 4 cambiaba el resultado para una celda de precio vacía (`""`) y **ninguna de mis pruebas lo habría detectado**, porque no tengo una prueba con precio vacío. Lo atrapó la revisión, no las pruebas. La próxima vez agregaría una prueba de caracterización para ese caso antes de refactorizar.

En la semana 7 rompí el código a propósito: las pruebas atraparon 4 de los 5 cambios. El quinto (`strip(" ")`, que deja los saltos de línea) no lo atrapó ninguna, y por eso se agregó el caso R2-13.

### Entrada 17

- **Fecha:** 2026-11-26
- **Prompt o sugerencia:** Le pedí a Claude convertir los criterios de HU-01 y HU-05 (reserva) en escenarios de aceptación (A-01 a A-15) y en pruebas automáticas (`tests/test_aceptacion.py`).
- **Decisión:** Aceptada con cambios
- **Por qué:** Al revisar cada prueba contra su escenario encontré que A-09 usaba la gorra (precio 0 y 5 unidades) y le ponía precio dentro de la prueba, así que el rechazo podía venir por falta de unidades y no por el máximo de 5. Además A-07, A-11 y A-12 solo comprobaban que hubo rechazo, sin revisar el motivo. Agregué al catálogo de prueba `ca-01` (8 unidades, $70.000), corregí A-09 y agregué un `assert` sobre el motivo en A-07, A-09, A-11 y A-12. También corregí mi propia clasificación: A-02, A-03, A-04 y A-07 sí se automatizan.
- **Verificación:** Clasifiqué los 15 escenarios (13 se automatizan, A-14 «le falta un dato», A-15 «no es observable»). Corrí `pytest -v` después de cada cambio: 72 pruebas pasan.
- **Commit relacionado:** `1b0a8a5`, `0f4d75e` y `ca79942`

### Entrada 18

- **Fecha:** 2026-11-26
- **Prompt o sugerencia:** Le pedí a Claude la función `crear_reserva` en `app/reservar.py`, que une `buscar_prenda` con mis 4 reglas de reservas, y la medición de cobertura con `pytest-cov`.
- **Decisión:** Aceptada con cambios (en las pruebas, no en el código)
- **Por qué:** La cobertura daba 98 %: la línea 57 («Falta el nombre del cliente») no tenía ningún escenario. Escribí A-16 (reserva sin nombre) y su prueba, y la cobertura quedó en 100 %. Al romper el código a propósito: cambiar `==` por `!=` en la forma de pago hizo fallar A-05, A-06 y A-13. Cambiar el texto «libres» del mensaje no hacía fallar ninguna prueba de la IA; con mi revisión fallan A-07, A-09 y A-12. También vi que el código usa un solo mensaje para tres motivos: al cliente de una prenda marcada «NO» le llega «quedan 0 libres» y nunca que no está disponible. Lo dejé anotado en el registro de la revisión.
- **Verificación:** `pytest --cov`: 72 passed, TOTAL 100 %. Deshice cada cambio con `git checkout app/reservar.py` y volví a correr las pruebas.
- **Commit relacionado:** `fdae80c` y `ca79942`

### Entrada 19

- **Fecha:** 2026-11-26
- **Prompt o sugerencia:** Le pedí a Claude redactar el reporte D-01 (precio vacío) a partir de los commits `ff05753` y `ea6db49` y de la entrada 7.
- **Decisión:** Aceptada con cambios
- **Por qué:** El borrador tenía datos que nadie comprobó: decía Python 3.11 (yo uso 3.13.15), «también se reproduce con Python 3.13 en Linux» (nadie lo probó) y «las 13 pruebas pasaban» (en `ff05753` eran 12, porque `test_precio_vacio_devuelve_none` se agregó después). No puse nombre de compañero porque trabajo solo en el taller.
- **Verificación:** Cloné el repo en una carpeta aparte, hice `git checkout ff05753`, corrí el comando del reporte y salió `'precio': ''`. Corrí `pytest tests/test_buscar_prenda.py` en esa copia: 12 passed.
- **Commit relacionado:** `8d8906d` y `ff5a65e`

## Reflexión semana 8

Esta bitácora me dejo ver algo muy valioso: que es el saber usar la IA como un apoyo y no como un reemplazo del  criterio. En lugar de quedarse uno con lo primero que te entregó, toca tomarse el trabajo de revisar a fondo y con seguridad, romper el código para ver si las pruebas de verdad servían y confirmar los datos en el historial de Git para no dejar mentiras en el reporte. Al final, la herramienta te ayudó a avanzar más rápido, pero lo que realmente le dio calidad y respaldo al proyecto fue el ojo crítico y el rigor al comprobar cada detalle.

## Entrada 20: pipeline de GitHub Actions generado con IA
- Herramienta: Claude, con el prompt simple de clase y sin contexto del repo.
- Revisión humana: 5 problemas (sin permisos, Python 3.9/3.10, pytest sin versión, requirements.txt inexistente, sin ruff ni cobertura).
- actionlint encontró 0.
- Al corregirlo, el pipeline atrapó un comentario de más de 88 caracteres en test_aceptacion.py que nadie había visto.
- Ejecución en verde: [https://github.com/Alexyulian19/SeminarioIA_Alexyulian21/actions/runs/45888663228?pr=4]

## Entrada 21: Dockerfile generado con IA
- Revisión humana: 5 puntos (imagen no slim, requirements.txt inexistente, COPY . . copiaba el .env con claves reales, corría como root; CMD pytest no era problema).
- hadolint encontró 1 (DL3042, pip sin --no-cache-dir).
- Corrección: imagen slim, usuario 10001, .dockerignore y copia solo de lo necesario.

## Reflexión semana 9
Si hubiera subido todo tal como lo dio la IA, habría tenido una falsa seguridad: el pipeline ni siquiera revisaba hubiera revisado bien el código y el Dockerfile dejabaria expuestas mis claves del .env corriendo como root. Lo más grave fue ese riesgo de seguridad y ver que los validadores automáticos solo atraparon 1 de 10 fallos; ya el resto los pude encontrar revisando a mano. Y como la IA no conoce los riesgos de mi proyecto ya que es de mi negocio estuve atento para prevenir por cualquier cosita o falla y ya para la próxima vez revisaré línea por línea qué archivos copia y qué permisos da antes de confiar en su código.

## Reflexión final (5 a 8 líneas)

El asistente me ayudó más a convertir el contrato en pruebas concretas y a escribir la implementación rápido, en un solo intento.
Lo que más aprendí fue a no aceptar todo: el primer contrato tenía un parámetro `color` que mi catálogo real no tiene, y una instrucción de git usaba una rama que no existía.
Usar el modo Manual de Claude Code me obligó a leer cada cambio antes de aceptarlo.
En el refactor vi la diferencia entre mejorar la estructura y cambiar el comportamiento: rechacé un cambio que parecía inofensivo porque alteraba el caso de una celda vacía.
Las pruebas pasaron siempre, pero eso me mostró que solo protegen lo que cubren.
En la próxima funcionalidad escribiría primero las pruebas de datos raros de la hoja (vacíos, espacios, mayúsculas) y revisaría el contrato contra los datos reales antes de pedir código.
En la semana 6 lo comprobé: un refactor con el mensaje «mismo comportamiento» pasó todas las pruebas y aun así cambió el resultado para un precio vacío.
Las pruebas en verde no demuestran que el comportamiento no cambió si ninguna cubre ese caso; antes de refactorizar escribiré primero las pruebas de esos casos.

**Semana 7.** Yo soy el que tiene la información del negocio: por mí pasa lo que se modifica y lo que no, y lo consulto con mi padre. Por eso las reglas y los esperados de las pruebas tienen que salir de mí, no de la IA.
Hacer las tablas me ayudó a pensar en problemas que no había pensado, como qué pasa a las 24 horas exactas o si el cliente escribe «Nequí», y me hace querer estar más atento a cualquier posible falla.
Me sorprendió que 54 pruebas en verde dejaran pasar un caso del agente de WhatsApp: el salto de línea al final del mensaje. Solo apareció cuando rompí el código a propósito.
La próxima vez me gustaría proponer yo mismo las pruebas que pueda identificar y apoyarme en la IA para hacerlas bien.

## Entrada: agente de WhatsApp funcionando en local (semana 10)

- **Fecha:** 2026-11-27
- **Prompt o sugerencia:** Le pedí a Claude construir el agente que faltaba: Claude (API de Anthropic) con 4 herramientas (`buscar_productos`, `consultar_prenda`, `crear_reserva`, `pasar_a_dueno`) sobre mis funciones de `app/`, un servidor FastAPI con el webhook de WhatsApp y un chat local tipo WhatsApp para la demo.
- **Qué hizo la IA:** escribió `app/catalogo.py`, `app/herramientas.py`, `app/agente.py`, `app/servidor.py`, `app/consola.py`, `app/web/chat.html`, las pruebas con un Claude falso (`tests/falsos.py` y 4 archivos de prueba, 67 pruebas nuevas), `requirements.txt`, `.env.example` y `docs/agente_whatsapp.md`. No cambió `buscar_prenda`, `reservas` ni `reservar`: el color se maneja filtrando el catálogo antes de llamarlas.
- **Supuestos que puso la IA y que debo decidir:** cantidad vacía = 5 unidades; reservas en memoria; esfuerzo bajo del modelo.
- **Decisión:** Acepto el agente y lo dejo con el chat local como demo.
- **Por qué:** Las pruebas pasan y en mi prueba real respondió bien a consultas y reservas sin inventar productos. Acepto por ahora los supuestos de cantidad vacía = 5 y reservas en memoria; Supabase queda para después.
- **Verificación:** `pytest --cov`: 147 passed, cobertura 100 %; `ruff check .` limpio. Prueba real en local con mi clave: el chat respondió con el catálogo real, preguntó el color y creó la reserva R-0001 (2 Adidas Campus, $260.000, Nequi), que apareció en el panel del dueño.
- **Problema con WhatsApp real:** Conecté el número de prueba de Meta con un túnel de cloudflared y el webhook quedó verificado, pero el agente no respondía. 1) No llegaban mensajes al servidor: publiqué la app en Meta y suscribí la cuenta de WhatsApp al webhook; desde ahí los mensajes sí llegaron. 2) El agente respondía pero el mensaje no aparecía en mi celular: agregué registro de errores al servidor y apareció el error 131031 «Business Account locked». 3) En Meta Business Support la cuenta sale «Cuenta restringida» con el aviso de que antes de enviar mensajes hay que verificar el negocio. Mi negocio sí está registrado, pero la verificación de Meta toma días, así que no alcanza para esta entrega. Guardé capturas como evidencia.
- **Mientras tanto:** Para la demo y la exposición uso el chat local (http://127.0.0.1:8000), que simula la conversación de WhatsApp con el mismo agente, el mismo formato y las mismas reservas. Cuando Meta verifique el negocio, solo cambia el canal y el agente sigue igual.
- **Commit relacionado:** rama `semana10-agente` (f1b0794 a la última)
## Entrada: Supabase en producción y prueba de punta a punta (semana 10)

- **Fecha:** 2026-11-27
- **Prompt o sugerencia:** Le pedí a Claude guardar las reservas en PostgreSQL de Supabase siguiendo mi modelo ER y publicar el chat para que el profesor lo pruebe desde su celular, entrando por el catálogo.
- **Qué hizo la IA:** `app/repositorio.py` (API REST de Supabase), `docs/supabase/crear_tablas.sql` con las tablas `reserva` y `linea_reserva`, RLS activo sin políticas públicas y la función `guardar_reserva`, que guarda la reserva y su línea en una sola transacción. También 8 pruebas con un HTTP falso (sin red), el panel del dueño con clave (`PANEL_CLAVE`), topes de mensajes y `render.yaml`. Las reglas de `reservas.py` no cambiaron. El SQL lo probó en PostgreSQL 16: si la línea falla, la reserva no queda.
- **Decisión:** Aceptada. Supabase quedó conectado en producción (Render) y el chat web propio queda como canal mientras Meta verifica el negocio.
- **Prueba real de punta a punta:** desde mi celular entré al catálogo en Netlify, elegí una prenda, el botón abrió el chat en Render con el mensaje escrito, hice la reserva y quedó guardada en Supabase (tablas `reserva` y `linea_reserva`) hoy a las 12:28 p. m.
- **WhatsApp real:** sigue bloqueado por Meta (error 131031, cuenta restringida hasta verificar el negocio; la verificación está pendiente). Por eso uso el chat web propio con el mismo agente: cuando Meta apruebe, solo cambia el canal.
- **Incidentes que encontré y resolví:**
  1. En mi `.env` la línea quedó `SUPABASE_URL=SUPABASE_URL=https://...` (prefijo pegado dos veces), así que la dirección no era válida. Lo corregí dejando un solo `SUPABASE_URL=`.
  2. En Render faltaban `SUPABASE_URL` y `SUPABASE_KEY`: el chat funcionaba, pero las reservas quedaban solo en memoria y se perdían al reiniciar. Agregué las dos variables en *Environment* y volví a desplegar.
  3. `APIConnectionError` con Anthropic: la clave había quedado mal copiada. La volví a pegar y respondió.
- **Lo que aprendí:** que las pruebas estén en verde no garantiza que la configuración esté bien. Los tres incidentes fueron de configuración (variables y claves), no de código, y solo aparecieron al probar el sistema completo de verdad.
- **Commit relacionado:** PR #7 (`semana10-agente`) y PR #8 (`semana10-supabase`); esta entrada va en la rama `semana10-cierre`.
