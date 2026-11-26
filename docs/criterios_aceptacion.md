# Criterios de aceptación automatizados (semana 8)

Proyecto: Agente de WhatsApp y catálogo web para Urban (SeminarioIA_Alexyulian21)
Estudiante: Alex Yulian Caviedes Córdoba
Fecha: 2026-11-26

Historias: **HU-01** (consultar disponibilidad y precio, Must) y **HU-05** (hacer el pedido por el chat, Must),
que desde la decisión del 31-oct-2026 es una **reserva**: sin pasarela de pago; efectivo en la tienda con
límite de 24 h, o transferencia por Nequi, Daviplata o Nu que el equipo verifica.

Los datos son sintéticos (catálogo de ejemplo y clientes ficticios de Neiva). Ninguna persona es real.

> Borrador generado con IA a partir de los criterios del documento de requisitos de la semana 3
> (CA-01.1 y CA-01.2), del contrato de HU-01 del README y de las reglas de `registro_pruebas.md`.
> La columna **Clasificación** la llena Alex al revisar: «se automatiza», «le falta un dato» o
> «no es observable».

## Datos de partida (catálogo de prueba)

| codigo | nombre | talla | precio | disponible | cantidad |
|---|---|---|---|---|---|
| th-01 | Tenis urbano blanco y dorado | 41 | 150000 | SI | 3 |
| je-01 | Jean azul clásico | 32 | 90000 | SI | 2 |
| go-01 | Gorra negra | UNICA | 0 (Consultar precio) | SI | 5 |
| bu-01 | Buso negro cuello redondo | M | 85000 | NO | 4 |
| ca-01 | Camiseta negra básica | M | 70000 | SI | 8 |
## HU-01: consultar si una prenda está disponible en mi talla y cuánto vale

| Id | Escenario | Clasificación (Alex) | Prueba |
|---|---|---|---|
| A-01 | **Prenda disponible (CA-01.1).** Dado que el «Tenis urbano blanco y dorado» (`th-01`) talla 41 tiene 3 unidades a $150.000 y no hay reservas, cuando el cliente pregunta por `th-01` en 41, entonces la respuesta dice que sí hay, con 3 unidades libres y precio $150.000. | Se automatiza | `test_a01_prenda_disponible` |
| A-02 | **Prenda que no está en el catálogo (CA-01.2).** Dado que el catálogo no tiene ninguna chaqueta de cuero, cuando el cliente pregunta por `ch-01` en L, entonces el sistema dice que no la tiene y no da ningún precio. | Se automatiza | 
`test_a02_prenda_que_no_esta` |
| A-03 | **Agotada por reservas (RNF-03).** Dado que el «Jean azul clásico» (`je-01`) talla 32 tiene 2 unidades y hay 2 reservas activas de 1 unidad, cuando el cliente pregunta por `je-01` en 32, entonces la respuesta dice que no hay y que quedan 0 libres. | Se automatiza | `test_a03_agotada_por_reservas` |
| A-04 | **Prenda a «Consultar precio».** Dado que la «Gorra negra» (`go-01`) tiene precio 0, cuando el cliente pregunta por ella, entonces hay unidades pero no se da ningún precio. | Se automatiza | `test_a04_consultar_precio` |

## HU-05: reservar una prenda por el chat

Contrato de la función que reúne las reglas (`app/reservar.py`):

```python
def crear_reserva(catalogo, reservas_activas, codigo, talla, cantidad,
                  forma_pago, cliente, ahora) -> dict
```

Devuelve la reserva nueva (`codigo`, `talla`, `nombre`, `cantidad`, `total`, `forma_pago`, `cliente`,
`creada_en` y `vence_en`), sin modificar las listas que recibe. `vence_en` es `creada_en` + 24 h si la
forma de pago es efectivo y `None` si es transferencia (la verifica el equipo). Lanza
`PrendaNoEncontrada` si la prenda no está y `ReservaRechazada` (con el motivo) si no se puede reservar.

| Id | Escenario | Clasificación (Alex) | Prueba |
|---|---|---|---|
| A-05 | **Reserva en efectivo.** Dado que `th-01` talla 41 tiene 3 unidades libres a $150.000, cuando «Valentina Rojas» reserva 2 para pagar en efectivo el 26-nov-2026 a las 10:00 a. m., entonces la reserva queda con total $300.000, vence el 27-nov-2026 a las 10:00 a. m. y a `th-01` en 41 le queda 1 unidad libre. | Se automatiza | `test_a05_reserva_en_efectivo` |
| A-06 | **Reserva por Nequi.** Dado lo mismo, cuando «Julián Cuéllar» reserva 1 y escribe « Nequi », entonces la reserva queda con forma de pago `nequi`, total $150.000 y sin hora de vencimiento. | Se automatiza | `test_a06_reserva_por_nequi` |
| A-07 | **Pide más de las que hay.** Dado que `je-01` talla 32 tiene 1 unidad libre, cuando un cliente intenta reservar 2, entonces el sistema la rechaza y sigue quedando 1 libre. | Se Automatiza | `test_a07_pide_mas_de_las_libres` |
| A-08 | **Pide justo las que quedan.** Dado que `je-01` talla 32 tiene 2 unidades libres, cuando un cliente reserva 2, entonces la reserva se acepta y la prenda queda agotada (0 libres). | Se automatiza | `test_a08_pide_justo_las_que_quedan` |
| A-09 | **Más de 5 unidades.** la Camiseta negra básica (ca-01) talla M tiene 8 unidades libres a $70.000, cuando un cliente intenta reservar 6, entonces el sistema la rechaza. | Se automatiza | `test_a09_mas_de_cinco_unidades` |
| A-10 | **«Transferencia» sin decir cuál.** Dado `th-01` en 41 con unidades, cuando el cliente escribe «transferencia», entonces el sistema la rechaza y el motivo pide elegir efectivo, Nequi, Daviplata o Nu. | Se automatiza | `test_a10_transferencia_sin_decir_cual` |
| A-11 | **Prenda a «Consultar precio».** Dado que la «Gorra negra» tiene precio 0, cuando un cliente intenta reservarla, entonces el sistema la rechaza porque no hay un precio para calcular el total. | Se automatiza | `test_a11_reserva_sin_precio` |
| A-12 | **Prenda marcada como no disponible.** Dado que el «Buso negro cuello redondo» (`bu-01`) talla M está en «NO», cuando un cliente intenta reservar 1, entonces el sistema la rechaza. | Se automatiza | `test_a12_prenda_no_disponible` |
| A-13 | **Vencimiento a las 24 h.** Dado que la reserva en efectivo de A-05 se creó el 26-nov-2026 a las 10:00 a. m., cuando son las 10:00 a. m. del 27-nov-2026, entonces la reserva está vencida. | Se automatiza | `test_a13_reserva_vence_a_las_24_horas` |
| A-14 | **Aviso al vencer.** Dado que una reserva en efectivo venció, cuando el sistema la cancela, entonces le avisa al cliente con el mensaje de cancelación. | Le Falta un Dato | sin prueba |
| A-15 | **Respuesta clara.** Dado que un cliente reserva por WhatsApp, cuando recibe la confirmación, entonces entiende fácilmente qué tiene que hacer para pagar. | No es Observable | sin prueba |
