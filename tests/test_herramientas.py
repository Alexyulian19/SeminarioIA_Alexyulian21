"""Pruebas de la tienda que ejecuta las herramientas del agente."""

import json
from datetime import datetime, timedelta

import pytest

from app.herramientas import HERRAMIENTAS, HORA_COLOMBIA, Tienda, ahora_colombia

INICIO = datetime(2026, 11, 27, 10, 0, tzinfo=HORA_COLOMBIA)


class Reloj:
    """Reloj que se puede adelantar a mano."""

    def __init__(self) -> None:
        self.ahora = INICIO

    def __call__(self) -> datetime:
        return self.ahora


@pytest.fixture
def reloj():
    return Reloj()


@pytest.fixture
def tienda(catalogo_prueba, reloj):
    return Tienda(catalogo_prueba, reloj)


def ejecutar(tienda, nombre, **entrada):
    contenido, es_error = tienda.ejecutar(nombre, entrada, "573000000000")
    return (contenido if es_error else json.loads(contenido)), es_error


def reservar(tienda, **cambios):
    datos = dict(codigo="th-08", talla="41", color="Suela beige", cantidad=1,
                 forma_pago="efectivo", cliente="Valentina Rojas")
    datos.update(cambios)
    return ejecutar(tienda, "crear_reserva", **datos)


def test_las_cuatro_herramientas_son_estrictas():
    nombres = [h["name"] for h in HERRAMIENTAS]
    assert nombres == ["buscar_productos", "consultar_prenda", "crear_reserva",
                       "pasar_a_dueno"]
    for h in HERRAMIENTAS:
        assert h["strict"] is True
        assert h["input_schema"]["additionalProperties"] is False


def test_hora_de_colombia_es_utc_menos_5():
    assert ahora_colombia().utcoffset() == timedelta(hours=-5)


def test_buscar_productos(tienda):
    resultado, es_error = ejecutar(tienda, "buscar_productos", texto="campus")
    assert not es_error
    assert resultado["productos"][0]["colores"] == ["Suela blanca", "Suela beige"]


def test_consultar_con_color_da_el_precio_de_ese_color(tienda):
    resultado, es_error = ejecutar(tienda, "consultar_prenda", codigo="th-08",
                                   talla="41", color="suela BEIGE")
    assert not es_error
    assert resultado["color"] == "Suela beige"
    assert resultado["precio"] == 135000
    assert resultado["unidades_libres"] == 2


def test_consultar_sin_color_cuando_hay_varios_pide_el_color(tienda):
    mensaje, es_error = ejecutar(tienda, "consultar_prenda", codigo="th-08",
                                 talla="41", color="")
    assert es_error
    assert "Suela blanca, Suela beige" in mensaje


def test_producto_sin_colores_no_necesita_color(tienda):
    resultado, _ = ejecutar(tienda, "consultar_prenda", codigo="je-01",
                            talla="32", color="")
    assert resultado["hay"] is True
    assert resultado["color"] == ""


def test_producto_de_un_solo_color_acepta_color_vacio(tienda):
    tienda.catalogo = [f for f in tienda.catalogo if f["color"] != "Suela beige"]
    resultado, _ = ejecutar(tienda, "consultar_prenda", codigo="th-08",
                            talla="40", color="")
    assert resultado["color"] == "Suela blanca"


def test_prenda_que_no_existe(tienda):
    mensaje, es_error = ejecutar(tienda, "consultar_prenda", codigo="ch-01",
                                 talla="L", color="")
    assert es_error
    assert "no está en el catálogo" in mensaje


def test_reserva_en_efectivo_vence_a_las_24_horas(tienda):
    reserva, es_error = reservar(tienda, cantidad=2)
    assert not es_error
    assert reserva["numero"] == "R-0001"
    assert reserva["total"] == 270000
    assert reserva["vence_en"] == "28-11-2026 10:00 AM"
    assert "chat_id" not in reserva
    assert tienda.reservas[0]["chat_id"] == "573000000000"


def test_la_reserva_descuenta_solo_su_color(tienda):
    reservar(tienda, cantidad=2)
    beige, _ = ejecutar(tienda, "consultar_prenda", codigo="th-08", talla="41",
                        color="Suela beige")
    blanca, _ = ejecutar(tienda, "consultar_prenda", codigo="th-08", talla="41",
                         color="Suela blanca")
    assert beige["hay"] is False
    assert blanca["unidades_libres"] == 5


def test_reserva_vencida_devuelve_las_unidades(tienda, reloj):
    reservar(tienda, cantidad=2)
    reloj.ahora = INICIO + timedelta(hours=24)
    beige, _ = ejecutar(tienda, "consultar_prenda", codigo="th-08", talla="41",
                        color="Suela beige")
    assert beige["unidades_libres"] == 2
    assert tienda.reservas_activas() == []


def test_reserva_por_nequi_no_vence(tienda, reloj):
    reserva, _ = reservar(tienda, forma_pago="Nequi")
    reloj.ahora = INICIO + timedelta(days=3)
    assert reserva["vence_en"] is None
    assert len(tienda.reservas_activas()) == 1


def test_transferencia_se_rechaza_y_pide_cual(tienda):
    mensaje, es_error = reservar(tienda, forma_pago="transferencia")
    assert es_error
    assert "efectivo, Nequi, Daviplata o Nu" in mensaje
    assert tienda.reservas == []


def test_mas_de_cinco_se_rechaza(tienda):
    mensaje, es_error = reservar(tienda, color="Suela blanca", cantidad=6)
    assert es_error
    assert "máximo 5" in mensaje


def test_prenda_sin_precio_no_se_reserva(tienda):
    mensaje, es_error = reservar(tienda, codigo="go-01", talla="UNICA", color="")
    assert es_error
    assert "no tiene precio" in mensaje


def test_cantidad_que_no_es_numero(tienda):
    mensaje, es_error = reservar(tienda, cantidad="dos")
    assert es_error
    assert "dos" in mensaje


def test_faltan_datos(tienda):
    mensaje, es_error = tienda.ejecutar("crear_reserva", {"codigo": "th-08"}, "x")
    assert es_error
    assert "Faltan datos" in mensaje


def test_pasar_a_dueno_queda_en_avisos(tienda):
    resultado, _ = ejecutar(tienda, "pasar_a_dueno", motivo="pide descuento")
    assert resultado == {"avisado": True}
    assert tienda.avisos_dueno[0]["motivo"] == "pide descuento"


def test_herramienta_desconocida(tienda):
    mensaje, es_error = tienda.ejecutar("borrar_todo", {}, "x")
    assert es_error
    assert "desconocida" in mensaje
