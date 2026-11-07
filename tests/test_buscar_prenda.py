"""Pruebas de HU-01: buscar_prenda (contrato en el README, sección «Funcionalidad de la semana 5»)."""

import copy

import pytest

from app.buscar_prenda import PrendaNoEncontrada, buscar_prenda


# ---------- Datos de prueba (códigos y tallas reales del catálogo, precios de ejemplo) ----------

def fila(codigo, nombre, talla, precio, disponible, cantidad):
    """Arma una fila de la lista del catálogo."""
    return {
        "codigo": codigo,
        "nombre": nombre,
        "talla": talla,
        "precio": precio,
        "disponible": disponible,
        "cantidad": cantidad,
    }


def reserva(codigo, talla, cantidad):
    """Arma una reserva activa."""
    return {"codigo": codigo, "talla": talla, "cantidad": cantidad}


@pytest.fixture
def catalogo():
    return [
        fila("th-01", "Tenis urbano blanco y dorado", "41", 150000, "SI", 3),
        fila("je-01", "Jean azul clásico", "32", 90000, "SI", 2),
        fila("bu-01", "Buso negro cuello redondo", "M", 85000, "NO", 4),
        fila("go-01", "Gorra negra", "UNICA", 0, "SI", 5),
    ]


# ---------- Casos normales ----------

def test_prenda_disponible_devuelve_nombre_precio_y_unidades(catalogo):
    # CA-01.1: hay la prenda en la talla y se dice el precio
    resultado = buscar_prenda(catalogo, [], "th-01", "41")

    assert resultado == {
        "nombre": "Tenis urbano blanco y dorado",
        "precio": 150000,
        "unidades_libres": 3,
        "hay": True,
    }


def test_resta_las_reservas_activas_de_la_misma_prenda_y_talla(catalogo):
    reservas = [
        reserva("je-01", "32", 1),
        reserva("je-01", "30", 1),   # otra talla: no se resta
        reserva("th-01", "32", 1),   # otra prenda: no se resta
    ]

    resultado = buscar_prenda(catalogo, reservas, "je-01", "32")

    assert resultado["unidades_libres"] == 1
    assert resultado["hay"] is True


# ---------- Casos límite ----------

def test_todas_las_unidades_reservadas_no_hay(catalogo):
    reservas = [reserva("je-01", "32", 1), reserva("je-01", "32", 1)]

    resultado = buscar_prenda(catalogo, reservas, "je-01", "32")

    assert resultado["unidades_libres"] == 0
    assert resultado["hay"] is False


def test_disponible_no_da_cero_aunque_haya_cantidad(catalogo):
    resultado = buscar_prenda(catalogo, [], "bu-01", "M")

    assert resultado["unidades_libres"] == 0
    assert resultado["hay"] is False


def test_mas_reservas_que_cantidad_nunca_da_negativo(catalogo):
    reservas = [reserva("je-01", "32", 3)]

    resultado = buscar_prenda(catalogo, reservas, "je-01", "32")

    assert resultado["unidades_libres"] == 0
    assert resultado["hay"] is False


def test_precio_cero_devuelve_none_para_consultar_precio(catalogo):
    resultado = buscar_prenda(catalogo, [], "go-01", "UNICA")

    assert resultado["precio"] is None
    assert resultado["unidades_libres"] == 5


def test_no_modifica_las_listas_que_recibe(catalogo):
    reservas = [reserva("th-01", "41", 1)]
    catalogo_antes = copy.deepcopy(catalogo)
    reservas_antes = copy.deepcopy(reservas)

    buscar_prenda(catalogo, reservas, "th-01", "41")

    assert catalogo == catalogo_antes
    assert reservas == reservas_antes


# ---------- Casos de error ----------

def test_prenda_que_no_esta_en_el_catalogo_lanza_error(catalogo):
    # CA-01.2: la chaqueta de cuero no existe; no se devuelve ningún precio
    with pytest.raises(PrendaNoEncontrada):
        buscar_prenda(catalogo, [], "ch-01", "L")


def test_talla_que_no_existe_lanza_error(catalogo):
    with pytest.raises(PrendaNoEncontrada):
        buscar_prenda(catalogo, [], "th-01", "45")


def test_catalogo_vacio_lanza_error():
    with pytest.raises(PrendaNoEncontrada):
        buscar_prenda([], [], "th-01", "41")