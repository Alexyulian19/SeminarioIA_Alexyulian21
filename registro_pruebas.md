# Registro de pruebas: tabla de casos y pruebas de la IA

Proyecto: Agente de WhatsApp y catálogo web para Urban (SeminarioIA_Alexyulian21)
Estudiante: Alex Yulian Caviedes Córdoba
Fecha: 2026-11-22

Funciones probadas: las cuatro de `app/reservas.py`, que el agente usa cuando un cliente quiere
reservar una prenda por WhatsApp. `buscar_prenda` (HU-01) ya tenía sus pruebas de las semanas 5 y 6
y no se tocó.

Las reglas salen de las decisiones del negocio (reserva sin pasarela de pago, efectivo en la tienda
con límite de 24 h, transferencia por Nequi, Daviplata o Nu que el equipo verifica) y de mis
respuestas del 22-nov-2026, que cito entre comillas.

## 1. Tabla de casos

### Regla 1: `reserva_vencida(creada_en, ahora)`, vencimiento de la reserva en efectivo

**Regla completa (el oráculo):** una reserva para pagar en efectivo en la tienda vence cuando se
cumplen 24 horas desde que se creó: «si vence a las 24 horas». Antes de las 24 h no está vencida;
a las 24 h exactas o después, sí. Si `ahora` es anterior a `creada_en`, es un error (`ValueError`),
porque una reserva no puede crearse en el futuro.

| # | Técnica | Partición o límite | Entrada (creada_en → ahora) | Esperado | Prueba que lo cubre |
|---|---|---|---|---|---|
| R1-1 | Partición válida | No vencida (menos de 24 h) | 21-nov 10:00 → 21-nov 12:00 (2 h) | False | `test_reserva_vencida[R1-1]` |
| R1-2 | Partición válida | Vencida (más de 24 h) | 21-nov 10:00 → 22-nov 16:00 (30 h) | True | `test_reserva_vencida[R1-2]` |
| R1-3 | Límite | Recién creada (0 s) | 21-nov 10:00 → 21-nov 10:00 | False | `test_reserva_vencida[R1-3]` |
| R1-4 | Límite | Último segundo antes de vencer | 21-nov 10:00 → 22-nov 09:59:59 | False | `test_reserva_vencida[R1-4]` |
| R1-5 | Límite | 24 h exactas | 21-nov 10:00 → 22-nov 10:00:00 | True | `test_reserva_vencida[R1-5]` |
| R1-6 | Límite | Primer segundo después de las 24 h | 21-nov 10:00 → 22-nov 10:00:01 | True | `test_reserva_vencida[R1-6]` |
| R1-7 | Partición inválida | `ahora` antes de `creada_en` | 21-nov 10:00 → 21-nov 09:00 | ValueError | `test_reserva_vencida_ahora_anterior_lanza_error[R1-7]` |
| R1-8 | Límite inválido | `ahora` un segundo antes de `creada_en` | 21-nov 10:00 → 21-nov 09:59:59 | ValueError | `test_reserva_vencida_ahora_anterior_lanza_error[R1-8]` |

**Ambigüedades encontradas:**
- ¿A las 24 h exactas ya venció? Resuelta: sí («vence a las 24 horas»), caso R1-5.
- ¿En qué zona horaria? Las dos fechas deben venir en la misma zona (hora de Colombia); la función no convierte zonas. Anotado como supuesto.
- La regla es solo para efectivo. Una reserva por transferencia no vence por esta función: la verifica el equipo. El agente solo la llama para reservas en efectivo.

### Regla 2: `normalizar_forma_pago(texto)`, forma de pago que escribe el cliente

**Regla completa (el oráculo):** las formas de pago aceptadas son efectivo, Nequi, Daviplata y Nu.
Con la forma elegida, «se le muestra el QR o se le pasa la cuenta correspondiente que quiera pagar el
cliente» y el equipo verifica antes de dar el pago por hecho. Se aceptan sin importar mayúsculas ni
espacios al inicio o al final, y se devuelven en minúscula: `"efectivo"`, `"nequi"`, `"daviplata"`
o `"nu"`. Cualquier otro texto, o texto vacío, es un error (`ValueError`): el agente le pregunta al
cliente cuál de las cuatro quiere.

| # | Técnica | Partición o límite | Entrada | Esperado | Prueba que lo cubre |
|---|---|---|---|---|---|
| R2-1 | Partición válida | Efectivo | `"efectivo"` | `"efectivo"` | `test_normalizar_forma_pago[R2-1]` |
| R2-2 | Partición válida | Nequi | `"nequi"` | `"nequi"` | `test_normalizar_forma_pago[R2-2]` |
| R2-3 | Partición válida | Daviplata | `"daviplata"` | `"daviplata"` | `test_normalizar_forma_pago[R2-3]` |
| R2-4 | Partición válida | Nu | `"nu"` | `"nu"` | `test_normalizar_forma_pago[R2-4]` |
| R2-5 | Partición válida | Mayúsculas | `"NEQUI"` | `"nequi"` | `test_normalizar_forma_pago[R2-5]` |
| R2-6 | Partición válida | Mayúscula inicial | `"Daviplata"` | `"daviplata"` | `test_normalizar_forma_pago[R2-6]` |
| R2-7 | Partición válida | Espacios a los lados | `"  efectivo "` | `"efectivo"` | `test_normalizar_forma_pago[R2-7]` |
| R2-8 | Partición inválida | Banco no aceptado | `"bancolombia"` | ValueError | `test_normalizar_forma_pago_invalida_lanza_error[R2-8]` |
| R2-9 | Partición inválida | «Transferencia» sin decir cuál | `"transferencia"` | ValueError | `test_normalizar_forma_pago_invalida_lanza_error[R2-9]` |
| R2-10 | Partición inválida | Nombre comercial con más palabras | `"Nu Bank"` | ValueError | `test_normalizar_forma_pago_invalida_lanza_error[R2-10]` |
| R2-11 | Límite (texto vacío) | Vacío | `""` | ValueError | `test_normalizar_forma_pago_invalida_lanza_error[R2-11]` |
| R2-12 | Límite (texto vacío) | Solo espacios | `"   "` | ValueError | `test_normalizar_forma_pago_invalida_lanza_error[R2-12]` |
| R2-14 | Partición inválida | Con tilde (decisión del 22-nov) | `"Nequí"` | ValueError | `test_normalizar_forma_pago_invalida_lanza_error[R2-14]` |
| R2-13 | Partición válida (agregada al romper el código) | Salto de línea al final, como cuando el cliente pulsa Enter | `"nequi\n"` | `"nequi"` | `test_normalizar_forma_pago[R2-13]` |

**Ambigüedades encontradas:**
- «Transferencia» sola: resuelta como ValueError; el agente pregunta cuál de las tres cuentas quiere.
- ¿Un salto de línea o una tabulación cuentan como «espacio»? Resuelta: sí, porque en WhatsApp el texto puede llegar con un salto de línea al final. Salió al romper el código (sección 3), caso R2-13.
- «Nu Bank» y «Nequí» (con tilde): **decidido, no se aceptan**. La cuenta se llama Nequi, sin tilde; si el cliente escribe «Nequí» o «Nu Bank», el agente le pide escribir Nequi, Daviplata, Nu o efectivo. Caso R2-14.

### Regla 3: `calcular_total(precio, cantidad)`, total de la reserva

**Regla completa (el oráculo):** el total es precio × cantidad, en pesos enteros.
- El precio mínimo de la tienda es 40.000: «el producto de mínimo valor es de 40.000 pesos, alguna
  gorra, ya de eso para arriba». Un precio menor que 40.000 es un error de la lista (`ValueError`).
- Precio `None` es «Consultar precio» (igual que en `buscar_prenda`): sin precio no hay total
  (`ValueError`).
- La cantidad va de 1 a 5 unidades de la misma prenda por reserva: «lo normal es 4 o 5 porque
  tampoco se tiene tanta mercancía». Cantidad menor que 1 o mayor que 5 es `ValueError`.

| # | Técnica | Partición o límite | Entrada (precio, cantidad) | Esperado | Prueba que lo cubre |
|---|---|---|---|---|---|
| R3-1 | Partición válida | Precio y cantidad normales | 80.000, 2 | 160.000 | `test_calcular_total[R3-1]` |
| R3-2 | Límite | Precio mínimo | 40.000, 1 | 40.000 | `test_calcular_total[R3-2]` |
| R3-3 | Límite | Un peso menos que el mínimo | 39.999, 1 | ValueError | `test_calcular_total_invalido_lanza_error[R3-3]` |
| R3-4 | Límite | Cantidad mínima | 150.000, 1 | 150.000 | `test_calcular_total[R3-4]` |
| R3-5 | Límite | Cantidad máxima | 150.000, 5 | 750.000 | `test_calcular_total[R3-5]` |
| R3-6 | Límite | Una más que el máximo | 150.000, 6 | ValueError | `test_calcular_total_invalido_lanza_error[R3-6]` |
| R3-7 | Límite | Cantidad cero | 150.000, 0 | ValueError | `test_calcular_total_invalido_lanza_error[R3-7]` |
| R3-8 | Partición inválida | Cantidad negativa | 150.000, −1 | ValueError | `test_calcular_total_invalido_lanza_error[R3-8]` |
| R3-9 | Partición inválida | Consultar precio | None, 1 | ValueError | `test_calcular_total_invalido_lanza_error[R3-9]` |
| R3-10 | Partición inválida | Precio 0 | 0, 1 | ValueError | `test_calcular_total_invalido_lanza_error[R3-10]` |

**Ambigüedades encontradas:**
- Máximo de unidades: dije «lo normal es 4 o 5». Se tomó **5** como máximo; confirmado: máximo 5, porque no se tiene tanta mercancía de una misma prenda.
- Precio 0: en `buscar_prenda` es «Consultar precio». Aquí da ValueError por ser menor que 40.000, que es el mismo resultado: sin precio no hay total.
- No hay decimales: los precios son pesos enteros, así que `pytest.approx` no aplica.

### Regla 4: `puede_reservar(disponible, unidades_libres, cantidad)`, si se acepta la reserva

**Regla completa (el oráculo):** se puede reservar si se cumplen las tres condiciones:
1. la prenda está disponible en la lista (`disponible == "SI"`),
2. la cantidad pedida está entre 1 y 5 (regla 3),
3. la cantidad pedida no supera las unidades libres: «si piden 1 o las que queden al momento, sí las
   puede pedir». Pedir exactamente las unidades que quedan sí se puede.

Si falla cualquiera, no se puede (False). Si `unidades_libres` es negativo, es un dato imposible
(`ValueError`).

| # | Técnica | Partición o límite | Entrada (disponible, libres, cantidad) | Esperado | Prueba que lo cubre |
|---|---|---|---|---|---|
| R4-1 | Límite | Pide exactamente las que quedan | "SI", 3, 3 | True | `test_puede_reservar_casos_de_limite[R4-1]` |
| R4-2 | Límite | Pide una más de las que quedan | "SI", 3, 4 | False | D2 (fila fusionada, ver sección 2) |
| R4-3 | Límite | Cantidad mínima | "SI", 3, 1 | True | `test_puede_reservar_casos_de_limite[R4-3]` |
| R4-4 | Límite | Cantidad cero | "SI", 3, 0 | False | `test_puede_reservar_casos_de_limite[R4-4]` |
| R4-5 | Límite | Cantidad máxima con stock | "SI", 8, 5 | True | `test_puede_reservar_casos_de_limite[R4-5]` |
| R4-6 | Límite | Una más que el máximo con stock | "SI", 8, 6 | False | D3 (fila fusionada, ver sección 2) |
| R4-7 | Límite | Agotada (0 libres) | "SI", 0, 1 | False | `test_puede_reservar_casos_de_limite[R4-7]` |
| R4-8 | Partición inválida | Disponible en minúscula | "si", 3, 1 | False | `test_puede_reservar_casos_de_limite[R4-8]` |
| R4-9 | Partición inválida | Libres negativo | "SI", −1, 1 | ValueError | `test_puede_reservar_libres_negativo_lanza_error` |

**Tabla de decisión** (C1: disponible es "SI"; C2: cantidad entre 1 y 5; C3: cantidad ≤ libres):

| # | C1 disponible | C2 cantidad 1–5 | C3 cantidad ≤ libres | Entrada | Esperado | Prueba que lo cubre |
|---|---|---|---|---|---|---|
| D1 | Sí | Sí | Sí | "SI", 3, 2 | True | `test_puede_reservar_tabla_de_decision[D1]` |
| D2 | Sí | Sí | No | "SI", 3, 4 | False | `test_puede_reservar_tabla_de_decision[D2]` |
| D3 | Sí | No | Sí | "SI", 8, 6 | False | `test_puede_reservar_tabla_de_decision[D3]` |
| D4 | Sí | No | No | "SI", 3, 6 | False | Descartada: redundante (sección 2) |
| D5 | No | Sí | Sí | "NO", 3, 2 | False | `test_puede_reservar_tabla_de_decision[D5]` |
| D6 | No | Sí | No | "NO", 1, 2 | False | Descartada: redundante (sección 2) |
| D7 | No | No | Sí | "NO", 10, 6 | False | Descartada: redundante (sección 2) |
| D8 | No | No | No | "NO", 3, 6 | False | Descartada: redundante (sección 2) |

Simplificación: si C1 es No, C2 y C3 no importan (D5 a D8 = False). Solo D1 da True. Como las tres
condiciones van unidas con «y», en las pruebas quedan D1 (todo se cumple) y una fila por cada condición
que falla sola: D2, D3 y D5. D2 y D3 usan los valores de borde (una más que las libres y una más que el
máximo). Por qué se descartaron D4, D6, D7 y D8: sección 2.

Nota: la cantidad 0 cumple C3 (0 ≤ libres) pero no C2, por eso R4-4 da False.

**Ambigüedades encontradas:**
- `"si"` en minúscula o con espacios: se mantiene la comparación exacta con `"SI"`, igual que en `buscar_prenda` (semana 5, entrada 8 de la bitácora). Decisión por confirmar cuando se lea la hoja de Google Sheets.
- ¿Cantidad mayor que 5 es error o solo «no se puede»? Aquí da False (el agente responde «máximo 5 por reserva»); en `calcular_total` es ValueError porque ese total nunca debería pedirse.

## 2. Pruebas de la IA descartadas o corregidas

**Prompt usado:** prompt 2 de la clase (rol: desarrollador que escribe pruebas con pytest; contexto:
`app/reservas.py` y este registro; tarea: una fila de `parametrize` por caso de las tablas y
`pytest.raises(ValueError)` para los errores; restricciones: no tocar `app/`, esperados fijos de la
regla, tipo de error exacto). Ver la entrada 13 de [bitacora_ia.md](bitacora_ia.md).

La salida de la IA está tal cual en el commit «Pruebas: test_reservas.py tal como lo generó la IA
(sin revisar)»: 47 pruebas, todas en verde, pero con 3 líneas que ruff marca como largas. La revisión
está en el commit siguiente: quedan 41 pruebas. Cada prueba se revisó con las tres preguntas:
¿el esperado sale de la regla?, ¿fallaría si rompo el código?, ¿cubre algo que otra no cubre?

Para la pregunta 2 en `puede_reservar` rompí cada condición por separado (la cambié por `True`) y
anoté qué filas fallaban:
- sin C1 (disponible): fallan R4-8 y D5;
- sin C2 (cantidad 1 a 5): fallan R4-4, R4-6 y D3;
- sin C3 (cantidad ≤ libres): fallan R4-2, R4-7 y D2.

D4, D6, D7 y D8 no fallaron con ninguno de los tres cambios.

| Prueba generada | Decisión | Por qué | En su lugar |
|---|---|---|---|
| Todas las de `parametrize` (ids automáticos como `[creada_en0-ahora0-False]`) | Corregida | Esperados correctos, pero con esos nombres no se puede saber qué fila de la tabla cubre cada prueba ni llenar la columna «Prueba que lo cubre» | `ids=["R1-1", ...]` con el código de la tabla; `pytest -v` ahora muestra `test_reserva_vencida[R1-5]` |
| Docstring del módulo y comentarios de R1-4 y R1-6 | Corregida | `ruff check` falla (E501, líneas de más de 88 caracteres) | Docstring en varias líneas y comentarios más cortos |
| Tabla de decisión D4 `("SI", 3, 6)` | Descartada | Pregunta 2: no falló al romper ninguna condición sola, porque siempre hay otra condición en No que da False. Pregunta 3: no cubre nada que D2 y D3 no cubran | Nada; la fila sigue en la tabla de decisión como «simplificada» |
| Tabla de decisión D6, D7 y D8 (`"NO"` con otras condiciones en No) | Descartada | Misma razón: con C1 en No el resultado es False sin importar C2 y C3 (la simplificación de la tabla). Solo D5 detecta que se quite C1 | D5 `("NO", 3, 2)` representa las filas con C1 en No |
| Límite R4-2 `("SI", 3, 4)` y tabla D2 `("SI", 1, 2)` | Corregida (fusionadas) | Las dos prueban la misma combinación (solo falla C3). Sobraba una, y la de la tabla no estaba en el borde | D2 usa la entrada del borde `("SI", 3, 4)` y se quitó R4-2 de la prueba de límites |
| Límite R4-6 `("SI", 8, 6)` y tabla D3 `("SI", 10, 6)` | Corregida (fusionadas) | Misma combinación (solo falla C2, por 6 unidades). Redundantes | D3 usa `("SI", 8, 6)` y se quitó R4-6 de la prueba de límites |
| Tabla D1 `("SI", 3, 2)` | Conservada | El mismo resultado que R4-1, R4-3 y R4-5, pero es la única fila «todo se cumple» de la tabla de decisión | — |
| Las 8 de `reserva_vencida` | Conservadas | Esperados de la regla (vence a las 24 h exactas: R1-5 es True). R1-4/R1-5 detectan si `>=` cambia a `>` o el límite cambia | — |
| Las 12 de `normalizar_forma_pago` | Conservadas | Una por partición; R2-5 y R2-7 detectan si se quita `.lower()` o `.strip()` | — |
| Las 10 de `calcular_total` | Conservadas | Esperados fijos (160.000, 40.000, 750.000), no `precio * cantidad`; los dos bordes de precio y de cantidad | — |

**Lo que la IA hizo bien:** usó `is True`/`is False` en lugar de `assert resultado`, `pytest.raises(ValueError)`
con el tipo exacto, esperados escritos como números y no tocó `app/`. No usó `pytest.approx` porque no hay
decimales (pesos enteros), como pide la regla.

**Lo que no se agregó:** una prueba unitaria para «Nequí» con tilde. La ambigüedad de la regla 2 sigue
abierta. En los datos sintéticos (sección 4) esa fila espera ValueError porque es lo que dice la regla
hoy. Si el negocio decide aceptarla, primero se cambia la regla y después el esperado.

## 3. Romper el código a propósito

Cada cambio se hizo solo, en `app/reservas.py`, se ejecutó `python -m pytest -q` y se deshizo con
`git restore app/reservas.py` antes del siguiente. Ninguno de estos cambios quedó en un commit.

| Cambio introducido | Archivo y línea | ¿Alguna prueba falló? | Qué hice |
|---|---|---|---|
| `cantidad <= unidades_libres` por `cantidad < unidades_libres` (no deja pedir las que quedan) | `app/reservas.py:95` | Sí, `test_puede_reservar_casos_de_limite[R4-1]` | Nada: la suite protege ese borde |
| `>= LIMITE_EFECTIVO` por `> LIMITE_EFECTIVO` (a las 24 h exactas no vencería) | `app/reservas.py:33` | Sí, `test_reserva_vencida[R1-5]` | Nada: la suite protege el borde de las 24 h |
| `precio * cantidad` por `precio + cantidad` | `app/reservas.py:74` | Sí, `test_calcular_total[R3-1]`, `[R3-2]`, `[R3-4]` y `[R3-5]` | Nada |
| `precio < PRECIO_MINIMO` por `precio <= PRECIO_MINIMO` (rechazaría la gorra de 40.000) | `app/reservas.py:70` | Sí, `test_calcular_total[R3-2]` | Nada: el borde de 40.000 está cubierto |
| `texto.strip()` por `texto.strip(" ")` (solo quita espacios, no saltos de línea) | `app/reservas.py:47` | **No**: 54 passed | Agregué R2-13 `"nequi\n"` → `"nequi"`. Con el código roto ahora falla `test_normalizar_forma_pago[R2-13]`; con el código bueno pasa |
| Cada condición de `puede_reservar` cambiada por `True`, una a la vez (ver sección 2) | `app/reservas.py:93-95` | Sí: sin C1 fallan R4-8 y D5; sin C2, R4-4 y D3; sin C3, R4-7 y D2 | Sirvió para descartar D4, D6, D7 y D8, que no fallaban con ninguno |

## 4. Datos de prueba

**Origen:** sintéticos generados con IA (Claude, prompt 3 de la clase adaptado a Urban: «tienda de ropa
urbana en Neiva que recibe reservas por WhatsApp…, ninguna persona real, teléfonos 300 000 xxxx»).
Confirmo que no hay datos de personas reales.

- Archivo: `tests/datos/reservas_sinteticas.csv` (20 filas). Columnas: cliente, barrio, telefono, codigo,
  talla, cantidad, forma_pago_escrita y forma_pago_esperada.
- Fixture: `reservas_sinteticas` en `tests/conftest.py`, que lee el CSV en UTF-8 con `csv.DictReader`.
- Pruebas que lo usan: `test_datos_sinteticos_son_ficticios` (20 filas, todos los teléfonos con el patrón
  300 000 xxxx) y `test_forma_de_pago_de_las_reservas_sinteticas`.
- La columna `forma_pago_esperada` no la generó la IA: se llenó con la regla 2 (ERROR = ValueError),
  para que el oráculo siga siendo la regla y no el código.
- Contexto local: barrios de Neiva (Altico, Cándido Leguízamo, Las Granjas, Timanco, Quirinal…), códigos de
  prenda del catálogo (th-01, je-01, bu-01, go-01), tallas reales (41, 32, M, UNICA) y cantidades de 1 a 5.

**Revisión de los datos generados:**
- Dos nombres llevaban apellidos del docente del seminario (Trujillo y Artunduaga). Los cambié por
  «Julián Andrés Cerquera» y «Juliana Motta Puentes» para que ningún dato se parezca a una persona real
  conocida.
- Revisé que ningún nombre fuera de una persona famosa y que los 20 teléfonos siguieran el patrón ficticio.

**Casos difíciles incluidos:**
- Tildes y ñ: «José Ángel Ñañez Bermúdez», «María Peña Sánchez», «Óscar Iván Muñoz».
- Apóstrofo: «Luz Dary D'Alessandro».
- Cliente vacío (fila 19): la forma de pago se sigue validando bien.
- Forma de pago vacía (fila 20) → ValueError.
- Salto de línea dentro de la celda (`"nequi\n"`, fila 17) y espacio de más (`"efectivo "`, `" nequi "`).
- Formas no aceptadas: «transferencia», «Bancolombia», «Nu Bank» y «Nequí» con tilde → ValueError.
- Mayúsculas: «NU», «DAVIPLATA», «Efectivo».
