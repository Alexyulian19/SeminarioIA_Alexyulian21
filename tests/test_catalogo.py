"""Pruebas de leer el catálogo CSV y buscar productos (app/catalogo.py)."""

import pytest

from app.catalogo import (
    CANTIDAD_SIN_DATO,
    MAX_RESULTADOS,
    buscar_productos,
    cargar_catalogo,
    colores_de,
    normalizar,
)
from tests.conftest import DATOS


def test_cargar_convierte_precio_y_cantidad(catalogo_prueba):
    jean = next(f for f in catalogo_prueba if f["codigo"] == "je-01")
    assert jean["precio"] == 90000
    assert jean["cantidad"] == 2


def test_cantidad_vacia_se_toma_como_cinco(catalogo_prueba):
    campus = catalogo_prueba[0]
    assert campus["cantidad"] == CANTIDAD_SIN_DATO == 5


def test_precio_vacio_queda_como_texto_vacio(tmp_path):
    ruta = tmp_path / "c.csv"
    ruta.write_text(
        "codigo,nombre,color,talla,precio,disponible,cantidad\n"
        "go-09,Gorra, ,UNICA,,SI ,1\n",
        encoding="utf-8",
    )
    fila = cargar_catalogo(ruta)[0]
    assert fila["precio"] == ""
    assert fila["color"] == ""
    assert fila["disponible"] == "SI"


def test_precio_con_letras_es_error(tmp_path):
    ruta = tmp_path / "c.csv"
    ruta.write_text(
        "codigo,nombre,color,talla,precio,disponible,cantidad\n"
        "go-09,Gorra,,UNICA,cuarenta,SI,1\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        cargar_catalogo(ruta)


def test_el_catalogo_real_de_la_web_se_puede_leer():
    catalogo = cargar_catalogo(DATOS.parent.parent / "datos" / "catalogo.csv")
    assert len(catalogo) > 100
    assert all(isinstance(f["cantidad"], int) for f in catalogo)


def test_normalizar_quita_tildes_y_mayusculas():
    assert normalizar("  Clásico ") == "clasico"


def test_colores_de_un_producto(catalogo_prueba):
    assert colores_de(catalogo_prueba, "th-08") == ["Suela blanca", "Suela beige"]
    assert colores_de(catalogo_prueba, "je-01") == []


def test_buscar_por_marca_agrupa_por_codigo(catalogo_prueba):
    resultado = buscar_productos(catalogo_prueba, "ADIDAS")
    assert len(resultado) == 1
    campus = resultado[0]
    assert campus["codigo"] == "th-08"
    assert campus["tallas"] == ["40", "41"]
    assert campus["precio"] == 130000


def test_buscar_sin_tilde_encuentra_con_tilde(catalogo_prueba):
    assert buscar_productos(catalogo_prueba, "jean clasico")[0]["codigo"] == "je-01"


def test_buscar_todas_las_palabras(catalogo_prueba):
    assert buscar_productos(catalogo_prueba, "adidas negro") == []


def test_producto_no_disponible_sale_sin_tallas(catalogo_prueba):
    buso = buscar_productos(catalogo_prueba, "buso")[0]
    assert buso["tallas"] == []


def test_producto_sin_precio_sale_con_none(catalogo_prueba):
    assert buscar_productos(catalogo_prueba, "gorra")[0]["precio"] is None


def test_buscar_devuelve_maximo_ocho(catalogo_prueba):
    muchos = [dict(catalogo_prueba[3], codigo=f"je-{i:02d}") for i in range(20)]
    assert len(buscar_productos(muchos, "jean")) == MAX_RESULTADOS
