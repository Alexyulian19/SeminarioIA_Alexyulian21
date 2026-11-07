"""HU-01: consultar si una prenda está disponible en una talla y cuánto vale.

El precio y las unidades salen siempre de la lista del catálogo y de las
reservas activas, nunca del modelo (RNF-03). Contrato en el README.
"""


class PrendaNoEncontrada(LookupError):
    """La prenda (código y talla) no está en la lista del catálogo."""


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
        (f for f in catalogo if f["codigo"] == codigo and f["talla"] == talla),
        None,
    )
    if fila is None:
        raise PrendaNoEncontrada(f"No hay {codigo} en talla {talla} en el catálogo")

    if fila["disponible"] == "SI":
        reservadas = sum(
            r["cantidad"]
            for r in reservas_activas
            if r["codigo"] == codigo and r["talla"] == talla
        )
        unidades_libres = max(fila["cantidad"] - reservadas, 0)
    else:
        unidades_libres = 0

    return {
        "nombre": fila["nombre"],
        "precio": fila["precio"] or None,
        "unidades_libres": unidades_libres,
        "hay": unidades_libres > 0,
    }
