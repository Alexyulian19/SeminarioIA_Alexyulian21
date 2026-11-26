"""HU-05: crear una reserva por el chat con las reglas de app/reservas.py.

Une buscar_prenda (HU-01) con las cuatro reglas de reservas. Función pura:
no lee la hoja ni la base de datos y no modifica las listas que recibe.
Escenarios de aceptación en docs/criterios_aceptacion.md.
"""

from datetime import datetime

from app.buscar_prenda import buscar_prenda
from app.reservas import (
    LIMITE_EFECTIVO,
    calcular_total,
    normalizar_forma_pago,
    puede_reservar,
)

FORMAS_PAGO_TEXTO = "efectivo, Nequi, Daviplata o Nu"


class ReservaRechazada(ValueError):
    """Error de que la reserva no se puede hacer; el mensaje dice el motivo."""


def crear_reserva(
    catalogo: list[dict],
    reservas_activas: list[dict],
    codigo: str,
    talla: str,
    cantidad: int,
    forma_pago: str,
    cliente: str,
    ahora: datetime,
) -> dict:
    """Crea una reserva si la prenda tiene unidades libres y los datos son válidos.

    Args:
        catalogo: filas de la lista del catálogo (ver buscar_prenda).
        reservas_activas: reservas sin vencer, con codigo, talla y cantidad.
        codigo: código de la prenda, por ejemplo "th-01".
        talla: talla como texto, por ejemplo "41".
        cantidad: unidades que pide el cliente, de 1 a 5.
        forma_pago: como la escribió el cliente, por ejemplo " Nequi ".
        cliente: nombre del cliente; no puede estar vacío.
        ahora: fecha y hora en que se crea la reserva (hora de Colombia).
    Returns:
        La reserva nueva: codigo, talla, nombre, cantidad, total, forma_pago,
        cliente, creada_en y vence_en (creada_en + 24 h si es efectivo; None si
        es transferencia, porque la verifica el equipo).
    Raises:
        PrendaNoEncontrada: si la prenda no está en el catálogo.
        ReservaRechazada: si falta el nombre, la forma de pago no es una de las
            cuatro, la prenda no tiene precio o no hay unidades suficientes.
    """
    nombre_cliente = cliente.strip()
    if not nombre_cliente:
        raise ReservaRechazada("Falta el nombre del cliente")

    try:
        forma = normalizar_forma_pago(forma_pago)
    except ValueError as error:
        raise ReservaRechazada(
            f"Elige una forma de pago: {FORMAS_PAGO_TEXTO}"
        ) from error

    prenda = buscar_prenda(catalogo, reservas_activas, codigo, talla)
    fila = next(
        f for f in catalogo if f["codigo"] == codigo and f["talla"] == talla
    )

    if not puede_reservar(fila["disponible"], prenda["unidades_libres"], cantidad):
        raise ReservaRechazada(
            f"No se puede reservar {cantidad} de {codigo} en talla {talla}: "
            f"quedan {prenda['unidades_libres']} libres (máximo 5 por reserva)"
        )

    try:
        total = calcular_total(prenda["precio"], cantidad)
    except ValueError as error:
        raise ReservaRechazada(
            f"{prenda['nombre']} no tiene precio: el equipo te lo confirma"
        ) from error

    return {
        "codigo": codigo,
        "talla": talla,
        "nombre": prenda["nombre"],
        "cantidad": cantidad,
        "total": total,
        "forma_pago": forma,
        "cliente": nombre_cliente,
        "creada_en": ahora,
        "vence_en": ahora + LIMITE_EFECTIVO if forma == "efectivo" else None,
    }
