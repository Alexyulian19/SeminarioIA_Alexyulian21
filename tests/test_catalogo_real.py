"""Pruebas contra el catálogo real (datos/catalogo.csv = el de la web v5).

Nacieron de un error real (27-nov-2026): el botón del catálogo web mandaba
"[bu-09] Camibuso Polo Dolce & Gabbana" y el agente no lo encontraba porque
su CSV era la copia vieja de 29 productos. Estas pruebas evitan que vuelva.
"""

import pytest

from app.catalogo import buscar_productos, cargar_catalogo, limpiar_codigo, palabras_de
from app.herramientas import Tienda
from tests.conftest import DATOS

CATALOGO = cargar_catalogo(DATOS.parent.parent / "datos" / "catalogo.csv")
PRODUCTOS = {f["codigo"]: f for f in reversed(CATALOGO)}  # primera fila de cada código


def test_el_catalogo_del_agente_es_el_de_la_web_v5():
    assert len(PRODUCTOS) == 71
    assert "bu-09" in PRODUCTOS


@pytest.mark.parametrize("codigo", sorted(PRODUCTOS))
def test_cada_producto_se_encuentra_por_codigo(codigo):
    resultado = buscar_productos(CATALOGO, codigo.upper())
    assert [p["codigo"] for p in resultado] == [codigo]


@pytest.mark.parametrize("codigo", sorted(PRODUCTOS))
def test_cada_producto_se_encuentra_con_el_mensaje_del_boton(codigo):
    fila = PRODUCTOS[codigo]
    mensaje = (f"Hola Urban, me interesa: [{codigo}] {fila['nombre']} color "
               f"{fila['color']} ({fila['marca']}, {fila['calidad']}) en talla "
               f"{fila['talla']}")
    resultado = buscar_productos(CATALOGO, mensaje)
    assert [p["codigo"] for p in resultado] == [codigo]


@pytest.mark.parametrize("codigo", sorted(PRODUCTOS))
def test_cada_producto_se_encuentra_por_su_nombre(codigo):
    resultado = buscar_productos(CATALOGO, PRODUCTOS[codigo]["nombre"])
    assert codigo in [p["codigo"] for p in resultado]


def test_dolce_gabbana_con_y_sin_ampersand():
    con = buscar_productos(CATALOGO, "polo Dolce & Gabbana")
    sin = buscar_productos(CATALOGO, "polo dolce gabbana")
    assert "bu-09" in [p["codigo"] for p in con]
    assert [p["codigo"] for p in con] == [p["codigo"] for p in sin]


def test_palabras_sin_signos():
    assert palabras_de("[BU-09] Polo, (Dolce & Gabbana)") == [
        "bu-09", "polo", "dolce", "&", "gabbana"]


def test_limpiar_codigo():
    assert limpiar_codigo(" [BU-09] ") == "bu-09"
    assert limpiar_codigo("") == ""


def test_consultar_bu_09_con_codigo_en_mayuscula_y_corchetes():
    tienda = Tienda(CATALOGO)
    resultado = tienda.consultar_prenda("[BU-09]", "m", "negro")
    assert resultado["codigo"] == "bu-09"
    assert resultado["talla"] == "M"
    assert resultado["color"] == "Negro"
    assert resultado["precio"] == 78000
