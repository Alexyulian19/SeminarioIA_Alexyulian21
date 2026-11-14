"""HU-01: consultar si una prenda está disponible en una talla y cuánto vale.

El precio y las unidades salen siempre de la lista del catálogo y de las
reservas activas, nunca del modelo (RNF-03). Contrato en el README.
"""

DISPONIBLE = "SI"
# Precio de la lista que significa «Consultar precio», igual que en la web.
PRECIO_CONSULTAR = 0


class PrendaNoEncontrada(LookupError):
    """Error de que la prenda (código y talla) no está en la lista del catálogo.

    Args:
        mensaje: texto que dice qué código y qué talla no se encontraron.
    Returns:
        No aplica: es una clase de excepción.
    Raises:
        No aplica: buscar_prenda es quien la lanza.
    """


def _es_misma_prenda(registro: dict, codigo: str, talla: str) -> bool:
    """Dice si una fila del catálogo o una reserva es de ese código y esa talla.

    Args:
        registro: fila del catálogo o reserva activa, con las claves codigo y talla.
        codigo: código de la prenda, por ejemplo "th-01".
        talla: talla como texto, por ejemplo "41" o "M".
    Returns:
        True si codigo y talla coinciden exactamente con los del registro;
        si no, False.
    Raises:
        KeyError: si el registro no tiene la clave codigo o talla.
    """
    return registro["codigo"] == codigo and registro["talla"] == talla


def _unidades_reservadas(reservas_activas: list[dict], codigo: str, talla: str) -> int:
    """Suma las unidades de las reservas activas de esa misma prenda y talla.

    Args:
        reservas_activas: reservas sin vencer, cada una con codigo, talla y cantidad.
        codigo: código de la prenda, por ejemplo "je-01".
        talla: talla como texto, por ejemplo "32".
    Returns:
        La suma de cantidad de las reservas con ese código y esa talla;
        0 si no hay ninguna.
    Raises:
        KeyError: si una reserva no tiene la clave codigo, talla o cantidad.
    """
    return sum(
        reserva["cantidad"]
        for reserva in reservas_activas
        if _es_misma_prenda(reserva, codigo, talla)
    )


def buscar_prenda(
    catalogo: list[dict],
    reservas_activas: list[dict],
    codigo: str,
    talla: str,
) -> dict:
    """Dice si hay unidades libres de una prenda en una talla y cuánto vale.

    No modifica las listas que recibe. Contrato completo en el README.

    Args:
        catalogo: filas de la lista del catálogo, ya leídas, una por producto y
            talla, con codigo, nombre, talla, precio (entero en pesos; 0 es
            «Consultar precio»), disponible («SI» o «NO») y cantidad. Si hubiera
            filas repetidas, usa la primera que coincide.
        reservas_activas: reservas sin vencer, cada una con codigo, talla y
            cantidad.
        codigo: código de la prenda en el catálogo, por ejemplo "th-01".
        talla: talla como texto, por ejemplo "41" o "M". La comparación es exacta.
    Returns:
        Diccionario con:
        - nombre: el nombre de la prenda en el catálogo.
        - precio: el precio de la fila en pesos, o None si es 0 o está vacío
          ("") («Consultar precio»).
        - unidades_libres: cantidad de la fila menos las reservadas de esa
          prenda y talla, nunca negativo; 0 si disponible no es «SI».
        - hay: True si unidades_libres es mayor que 0; si no, False.
    Raises:
        PrendaNoEncontrada: si ninguna fila del catálogo tiene ese código y esa
            talla (también si el catálogo está vacío).
        KeyError: si una fila o una reserva que se revisa no tiene una de las
            claves anteriores.
    """
    fila = next(
        (
            fila_catalogo
            for fila_catalogo in catalogo
            if _es_misma_prenda(fila_catalogo, codigo, talla)
        ),
        None,
    )
    if fila is None:
        raise PrendaNoEncontrada(f"No hay {codigo} en talla {talla} en el catálogo")

    unidades_libres = 0
    if fila["disponible"] == DISPONIBLE:
        reservadas = _unidades_reservadas(reservas_activas, codigo, talla)
        unidades_libres = max(fila["cantidad"] - reservadas, 0)

    precio = None if fila["precio"] in (PRECIO_CONSULTAR, "") else fila["precio"]

    return {
        "nombre": fila["nombre"],
        "precio": precio,
        "unidades_libres": unidades_libres,
        "hay": unidades_libres > 0,
    }
