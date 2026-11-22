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

### Regla 2: `normalizar_forma_pago(texto)`, forma de pago que escribe el cliente

**Regla completa (el oráculo):** las formas de pago aceptadas son efectivo, Nequi, Daviplata y Nu.
Con la forma elegida, «se le muestra el QR o se le pasa la cuenta correspondiente que quiera pagar el
cliente» y el equipo verifica antes de dar el pago por hecho. Se aceptan sin importar mayúsculas ni
espacios al inicio o al final, y se devuelven en minúscula: `"efectivo"`, `"nequi"`, `"daviplata"`
o `"nu"`. Cualquier otro texto, o texto vacío, es un error (`ValueError`): el agente le pregunta al
cliente cuál de las cuatro quiere.

### Regla 3: `calcular_total(precio, cantidad)`, total de la reserva

**Regla completa (el oráculo):** el total es precio × cantidad, en pesos enteros.
- El precio mínimo de la tienda es 40.000: «el producto de mínimo valor es de 40.000 pesos, alguna
  gorra, ya de eso para arriba». Un precio menor que 40.000 es un error de la lista (`ValueError`).
- Precio `None` es «Consultar precio» (igual que en `buscar_prenda`): sin precio no hay total
  (`ValueError`).
- La cantidad va de 1 a 5 unidades de la misma prenda por reserva: «lo normal es 4 o 5 porque
  tampoco se tiene tanta mercancía». Cantidad menor que 1 o mayor que 5 es `ValueError`.

### Regla 4: `puede_reservar(disponible, unidades_libres, cantidad)`, si se acepta la reserva

**Regla completa (el oráculo):** se puede reservar si se cumplen las tres condiciones:
1. la prenda está disponible en la lista (`disponible == "SI"`),
2. la cantidad pedida está entre 1 y 5 (regla 3),
3. la cantidad pedida no supera las unidades libres: «si piden 1 o las que queden al momento, sí las
   puede pedir». Pedir exactamente las unidades que quedan sí se puede.

Si falla cualquiera, no se puede (False). Si `unidades_libres` es negativo, es un dato imposible
(`ValueError`).
