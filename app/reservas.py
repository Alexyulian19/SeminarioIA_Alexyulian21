"""Reglas de las reservas por WhatsApp: vencimiento, forma de pago, total y stock.

Funciones puras: no leen la hoja ni la base de datos; reciben los datos ya leídos.
Las reglas (el oráculo de las pruebas) están en registro_pruebas.md, sección 1.
"""

from datetime import datetime, timedelta

from app.buscar_prenda import DISPONIBLE

# Una reserva en efectivo vence al cumplir 24 h desde que se creó.
LIMITE_EFECTIVO = timedelta(hours=24)
FORMAS_PAGO = frozenset({"efectivo", "nequi", "daviplata", "nu"})
# Precio de la prenda más barata de la tienda (una gorra).
PRECIO_MINIMO = 40_000
CANTIDAD_MINIMA = 1
CANTIDAD_MAXIMA = 5


def reserva_vencida(creada_en: datetime, ahora: datetime) -> bool:
    """Dice si una reserva para pagar en efectivo ya venció.

    Args:
        creada_en: fecha y hora en que se creó la reserva.
        ahora: fecha y hora actual, en la misma zona horaria que creada_en.
    Returns:
        True si pasaron 24 h o más desde creada_en; si no, False.
    Raises:
        ValueError: si ahora es anterior a creada_en.
    """
    if ahora < creada_en:
        raise ValueError("ahora no puede ser anterior a la creación de la reserva")
    return ahora - creada_en >= LIMITE_EFECTIVO


def normalizar_forma_pago(texto: str) -> str:
    """Convierte la forma de pago que escribe el cliente en una de las aceptadas.

    Args:
        texto: forma de pago como la escribió el cliente, por ejemplo " Nequi ".
    Returns:
        "efectivo", "nequi", "daviplata" o "nu".
    Raises:
        ValueError: si el texto, sin espacios a los lados y en minúscula, no es
            una de las cuatro formas aceptadas (incluye el texto vacío).
    """
    forma = texto.strip().lower()
    if forma not in FORMAS_PAGO:
        raise ValueError(f"Forma de pago no aceptada: {texto!r}")
    return forma


def _cantidad_valida(cantidad: int) -> bool:
    """Dice si la cantidad está entre CANTIDAD_MINIMA y CANTIDAD_MAXIMA."""
    return CANTIDAD_MINIMA <= cantidad <= CANTIDAD_MAXIMA


def calcular_total(precio: int | None, cantidad: int) -> int:
    """Calcula el total de una reserva en pesos.

    Args:
        precio: precio de la prenda en pesos enteros; None es «Consultar precio».
        cantidad: unidades de la misma prenda, de 1 a 5.
    Returns:
        precio × cantidad.
    Raises:
        ValueError: si precio es None o menor que 40.000, o si cantidad no está
            entre 1 y 5.
    """
    if precio is None or precio < PRECIO_MINIMO:
        raise ValueError("La prenda no tiene un precio válido para calcular el total")
    if not _cantidad_valida(cantidad):
        raise ValueError("La cantidad debe estar entre 1 y 5")
    return precio * cantidad


def puede_reservar(disponible: str, unidades_libres: int, cantidad: int) -> bool:
    """Dice si se acepta una reserva de una prenda.

    Args:
        disponible: columna disponible de la lista («SI» o «NO»), comparación exacta.
        unidades_libres: unidades sin reservar de esa prenda y talla.
        cantidad: unidades que pide el cliente.
    Returns:
        True si disponible es «SI», la cantidad está entre 1 y 5 y no supera las
        unidades libres; si no, False.
    Raises:
        ValueError: si unidades_libres es negativo.
    """
    if unidades_libres < 0:
        raise ValueError("unidades_libres no puede ser negativo")
    return (
        disponible == DISPONIBLE
        and _cantidad_valida(cantidad)
        and cantidad <= unidades_libres
    )
