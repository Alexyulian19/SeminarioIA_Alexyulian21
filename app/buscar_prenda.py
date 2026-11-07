"""HU-01: consultar si una prenda está disponible en una talla y cuánto vale.

Por ahora solo tiene la firma del contrato. La implementación va en el paso 3.
"""


class PrendaNoEncontrada(LookupError):
    """La prenda (código y talla) no está en la lista del catálogo."""


def buscar_prenda(
    catalogo: list[dict],
    reservas_activas: list[dict],
    codigo: str,
    talla: str,
) -> dict:
    """Devuelve nombre, precio, unidades_libres y hay. Ver el contrato en el README."""
    raise NotImplementedError("Pendiente: se implementa en el paso 3")