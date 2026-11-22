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
| R1-1 | Partición válida | No vencida (menos de 24 h) | 21-nov 10:00 → 21-nov 12:00 (2 h) | False | (paso 4) |
| R1-2 | Partición válida | Vencida (más de 24 h) | 21-nov 10:00 → 22-nov 16:00 (30 h) | True | (paso 4) |
| R1-3 | Límite | Recién creada (0 s) | 21-nov 10:00 → 21-nov 10:00 | False | (paso 4) |
| R1-4 | Límite | Último segundo antes de vencer | 21-nov 10:00 → 22-nov 09:59:59 | False | (paso 4) |
| R1-5 | Límite | 24 h exactas | 21-nov 10:00 → 22-nov 10:00:00 | True | (paso 4) |
| R1-6 | Límite | Primer segundo después de las 24 h | 21-nov 10:00 → 22-nov 10:00:01 | True | (paso 4) |
| R1-7 | Partición inválida | `ahora` antes de `creada_en` | 21-nov 10:00 → 21-nov 09:00 | ValueError | (paso 4) |
| R1-8 | Límite inválido | `ahora` un segundo antes de `creada_en` | 21-nov 10:00 → 21-nov 09:59:59 | ValueError | (paso 4) |

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
| R2-1 | Partición válida | Efectivo | `"efectivo"` | `"efectivo"` | (paso 4) |
| R2-2 | Partición válida | Nequi | `"nequi"` | `"nequi"` | (paso 4) |
| R2-3 | Partición válida | Daviplata | `"daviplata"` | `"daviplata"` | (paso 4) |
| R2-4 | Partición válida | Nu | `"nu"` | `"nu"` | (paso 4) |
| R2-5 | Partición válida | Mayúsculas | `"NEQUI"` | `"nequi"` | (paso 4) |
| R2-6 | Partición válida | Mayúscula inicial | `"Daviplata"` | `"daviplata"` | (paso 4) |
| R2-7 | Partición válida | Espacios a los lados | `"  efectivo "` | `"efectivo"` | (paso 4) |
| R2-8 | Partición inválida | Banco no aceptado | `"bancolombia"` | ValueError | (paso 4) |
| R2-9 | Partición inválida | «Transferencia» sin decir cuál | `"transferencia"` | ValueError | (paso 4) |
| R2-10 | Partición inválida | Nombre comercial con más palabras | `"Nu Bank"` | ValueError | (paso 4) |
| R2-11 | Límite (texto vacío) | Vacío | `""` | ValueError | (paso 4) |
| R2-12 | Límite (texto vacío) | Solo espacios | `"   "` | ValueError | (paso 4) |

**Ambigüedades encontradas:**
- «Transferencia» sola: resuelta como ValueError; el agente pregunta cuál de las tres cuentas quiere.
- «Nu Bank» y «Nequí» (con tilde): **abiertas**. Por ahora son ValueError porque la regla solo acepta los cuatro nombres exactos; queda por confirmar con el negocio si se aceptan esas variantes.

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
| R3-1 | Partición válida | Precio y cantidad normales | 80.000, 2 | 160.000 | (paso 4) |
| R3-2 | Límite | Precio mínimo | 40.000, 1 | 40.000 | (paso 4) |
| R3-3 | Límite | Un peso menos que el mínimo | 39.999, 1 | ValueError | (paso 4) |
| R3-4 | Límite | Cantidad mínima | 150.000, 1 | 150.000 | (paso 4) |
| R3-5 | Límite | Cantidad máxima | 150.000, 5 | 750.000 | (paso 4) |
| R3-6 | Límite | Una más que el máximo | 150.000, 6 | ValueError | (paso 4) |
| R3-7 | Límite | Cantidad cero | 150.000, 0 | ValueError | (paso 4) |
| R3-8 | Partición inválida | Cantidad negativa | 150.000, −1 | ValueError | (paso 4) |
| R3-9 | Partición inválida | Consultar precio | None, 1 | ValueError | (paso 4) |
| R3-10 | Partición inválida | Precio 0 | 0, 1 | ValueError | (paso 4) |

**Ambigüedades encontradas:**
- Máximo de unidades: dije «lo normal es 4 o 5». Se tomó **5** como máximo; queda por confirmar si en algún caso se permite más.
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
| R4-1 | Límite | Pide exactamente las que quedan | "SI", 3, 3 | True | (paso 4) |
| R4-2 | Límite | Pide una más de las que quedan | "SI", 3, 4 | False | (paso 4) |
| R4-3 | Límite | Cantidad mínima | "SI", 3, 1 | True | (paso 4) |
| R4-4 | Límite | Cantidad cero | "SI", 3, 0 | False | (paso 4) |
| R4-5 | Límite | Cantidad máxima con stock | "SI", 8, 5 | True | (paso 4) |
| R4-6 | Límite | Una más que el máximo con stock | "SI", 8, 6 | False | (paso 4) |
| R4-7 | Límite | Agotada (0 libres) | "SI", 0, 1 | False | (paso 4) |
| R4-8 | Partición inválida | Disponible en minúscula | "si", 3, 1 | False | (paso 4) |
| R4-9 | Partición inválida | Libres negativo | "SI", −1, 1 | ValueError | (paso 4) |

**Tabla de decisión** (C1: disponible es "SI"; C2: cantidad entre 1 y 5; C3: cantidad ≤ libres):

| # | C1 disponible | C2 cantidad 1–5 | C3 cantidad ≤ libres | Entrada | Esperado |
|---|---|---|---|---|---|
| D1 | Sí | Sí | Sí | "SI", 3, 2 | True |
| D2 | Sí | Sí | No | "SI", 1, 2 | False |
| D3 | Sí | No | Sí | "SI", 10, 6 | False |
| D4 | Sí | No | No | "SI", 3, 6 | False |
| D5 | No | Sí | Sí | "NO", 3, 2 | False |
| D6 | No | Sí | No | "NO", 1, 2 | False |
| D7 | No | No | Sí | "NO", 10, 6 | False |
| D8 | No | No | No | "NO", 3, 6 | False |

Simplificación: si C1 es No, C2 y C3 no importan (D5 a D8 = False). Solo D1 da True. Se dejan las 8
filas en las pruebas porque cada una se escribe en una línea de `parametrize`.

Nota: la cantidad 0 cumple C3 (0 ≤ libres) pero no C2, por eso R4-4 da False.

**Ambigüedades encontradas:**
- `"si"` en minúscula o con espacios: se mantiene la comparación exacta con `"SI"`, igual que en `buscar_prenda` (semana 5, entrada 8 de la bitácora). Decisión por confirmar cuando se lea la hoja de Google Sheets.
- ¿Cantidad mayor que 5 es error o solo «no se puede»? Aquí da False (el agente responde «máximo 5 por reserva»); en `calcular_total` es ValueError porque ese total nunca debería pedirse.
