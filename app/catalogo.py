"""Leer el catálogo (CSV exportado de la hoja o de la web) y buscar en él.

El catálogo tiene una fila por producto, color y talla, con las columnas de la
web: codigo, nombre, categoria, marca, color, talla, precio, disponible y
cantidad (las demás columnas se conservan pero no se usan aquí).
"""

import csv
import unicodedata
from pathlib import Path

from app.buscar_prenda import DISPONIBLE

# Supuesto por validar con Alex: hoy la columna cantidad está vacía porque no
# se lleva inventario. Vacía se toma como 5 (el máximo de una reserva).
CANTIDAD_SIN_DATO = 5
MAX_RESULTADOS = 8


def cargar_catalogo(ruta: Path | str) -> list[dict]:
    """Lee el CSV del catálogo y deja precio y cantidad como enteros.

    Args:
        ruta: ruta del archivo CSV en UTF-8 con encabezados.
    Returns:
        Lista de filas (diccionarios). precio es entero, o "" si está vacío;
        cantidad es entero, o CANTIDAD_SIN_DATO si está vacía. color, talla y
        disponible quedan sin espacios a los lados.
    Raises:
        FileNotFoundError: si el archivo no existe.
        ValueError: si precio o cantidad no son números.
    """
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    for fila in filas:
        for clave in ("codigo", "talla", "color", "disponible"):
            fila[clave] = (fila.get(clave) or "").strip()
        precio = (fila.get("precio") or "").strip()
        fila["precio"] = int(precio) if precio else ""
        cantidad = (fila.get("cantidad") or "").strip()
        fila["cantidad"] = int(cantidad) if cantidad else CANTIDAD_SIN_DATO
    return filas


def normalizar(texto: str) -> str:
    """Pasa a minúscula y quita tildes y espacios a los lados ("Beige " -> "beige")."""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return sin_tildes.strip().casefold()


def colores_de(catalogo: list[dict], codigo: str) -> list[str]:
    """Colores distintos de un código, en el orden del catálogo ("" no cuenta)."""
    colores: list[str] = []
    for fila in catalogo:
        if fila["codigo"] == codigo and fila["color"] and fila["color"] not in colores:
            colores.append(fila["color"])
    return colores


def buscar_productos(catalogo: list[dict], texto: str) -> list[dict]:
    """Busca productos cuyo código, nombre, marca, categoría o color tenga las palabras.

    Args:
        catalogo: filas ya leídas con cargar_catalogo.
        texto: lo que escribe el cliente, por ejemplo "tenis adidas negro".
            Cada palabra debe aparecer (sin importar tildes ni mayúsculas).
    Returns:
        Hasta MAX_RESULTADOS productos (uno por código), cada uno con codigo,
        nombre, marca, categoria, colores, tallas (solo las disponibles) y
        precio (el más bajo de sus filas, None si es «Consultar precio»).
    """
    palabras = normalizar(texto).split()
    productos: dict[str, dict] = {}
    for fila in catalogo:
        campos = " ".join(
            fila.get(c) or "" for c in ("codigo", "nombre", "marca", "categoria",
                                         "tipo", "color")
        )
        if not all(p in normalizar(campos) for p in palabras):
            continue
        producto = productos.setdefault(fila["codigo"], {
            "codigo": fila["codigo"],
            "nombre": fila["nombre"],
            "marca": fila.get("marca", ""),
            "categoria": fila.get("categoria", ""),
            "colores": [],
            "tallas": [],
            "precio": None,
        })
        if fila["color"] and fila["color"] not in producto["colores"]:
            producto["colores"].append(fila["color"])
        if fila["disponible"] == DISPONIBLE and fila["talla"] not in producto["tallas"]:
            producto["tallas"].append(fila["talla"])
        if fila["precio"]:
            precio = producto["precio"]
            producto["precio"] = fila["precio"] if precio is None else min(
                precio, fila["precio"]
            )
    return list(productos.values())[:MAX_RESULTADOS]
