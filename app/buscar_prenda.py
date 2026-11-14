"""HU-01: consultar si una prenda está disponible en una talla y cuánto vale.

El precio y las unidades salen siempre de la lista del catálogo y de las
reservas activas, nunca del modelo (RNF-03). Contrato en el README.
"""

DISPONIBLE = "SI"
# Precio de la lista que significa «Consultar precio», igual que en la web.
PRECIO_CONSULTAR = 0


class PrendaNoEncontrada(LookupError):
    """La prenda (código y talla) no está en la lista del catálogo."""


def _unidades_reservadas(reservas_activas: list[dict], codigo: str, talla: str) -> int:
    """Suma las unidades de las reservas activas de esa misma prenda y talla."""
    return sum(
        reserva["cantidad"]
        for reserva in reservas_activas
        if reserva["codigo"] == codigo and reserva["talla"] == talla
    )


def buscar_prenda(
    catalogo: list[dict],
    reservas_activas: list[dict],
    codigo: str,
    talla: str,
) -> dict:
    """Devuelve nombre, precio, unidades_libres y hay. Ver el contrato en el README.

    Lanza PrendaNoEncontrada si no hay ninguna fila con ese código y esa talla.
    No modifica las listas que recibe.
    """
    fila = next(
        (
            fila_catalogo
            for fila_catalogo in catalogo
            if fila_catalogo["codigo"] == codigo and fila_catalogo["talla"] == talla
        ),
        None,
    )
    if fila is None:
        raise PrendaNoEncontrada(f"No hay {codigo} en talla {talla} en el catálogo")

    unidades_libres = 0
    if fila["disponible"] == DISPONIBLE:
        reservadas = _unidades_reservadas(reservas_activas, codigo, talla)
        unidades_libres = max(fila["cantidad"] - reservadas, 0)

    precio = None if fila["precio"] == PRECIO_CONSULTAR else fila["precio"]

    return {
        "nombre": fila["nombre"],
        "precio": precio,
        "unidades_libres": unidades_libres,
        "hay": unidades_libres > 0,
    }
