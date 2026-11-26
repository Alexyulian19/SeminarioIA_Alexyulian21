"""Pruebas de aceptación de HU-01 y HU-05 (reserva).

Cada prueba es un escenario de docs/criterios_aceptacion.md, con sus datos exactos.
Los comentarios Dado, Cuando y Entonces siguen el texto del criterio.
Datos sintéticos: ninguna persona ni teléfono es real.
"""

from datetime import datetime, timedelta

import pytest

from app.buscar_prenda import PrendaNoEncontrada, buscar_prenda
from app.reservar import ReservaRechazada, crear_reserva
from app.reservas import reserva_vencida

AHORA = datetime(2026, 11, 26, 10, 0)


@pytest.fixture
def catalogo() -> list[dict]:
    """Catálogo de prueba de docs/criterios_aceptacion.md."""
    return [
        {"codigo": "th-01", "nombre": "Tenis urbano blanco y dorado", "talla": "41",
         "precio": 150000, "disponible": "SI", "cantidad": 3},
        {"codigo": "je-01", "nombre": "Jean azul clásico", "talla": "32",
         "precio": 90000, "disponible": "SI", "cantidad": 2},
        {"codigo": "go-01", "nombre": "Gorra negra", "talla": "UNICA",
         "precio": 0, "disponible": "SI", "cantidad": 5},
        {"codigo": "bu-01", "nombre": "Buso negro cuello redondo", "talla": "M",
         "precio": 85000, "disponible": "NO", "cantidad": 4},
                {"codigo": "ca-01", "nombre": "Camiseta negra básica", "talla": "M",
         "precio": 70000, "disponible": "SI", "cantidad": 8},
    ]


def _reserva(codigo: str, talla: str, cantidad: int) -> dict:
    return {"codigo": codigo, "talla": talla, "cantidad": cantidad}


# ---------- HU-01 ----------


def test_a01_prenda_disponible(catalogo):
    # Dado: th-01 talla 41 con 3 unidades a $150.000 y sin reservas
    # Cuando: el cliente pregunta por th-01 en 41
    respuesta = buscar_prenda(catalogo, [], "th-01", "41")
    # Entonces: sí hay, 3 libres, precio $150.000
    assert respuesta == {
        "nombre": "Tenis urbano blanco y dorado",
        "precio": 150000,
        "unidades_libres": 3,
        "hay": True,
    }


def test_a02_prenda_que_no_esta(catalogo):
    # Dado: el catálogo no tiene ninguna chaqueta de cuero
    # Cuando: el cliente pregunta por ch-01 en L
    # Entonces: el sistema dice que no la tiene y no da ningún precio
    with pytest.raises(PrendaNoEncontrada) as error:
        buscar_prenda(catalogo, [], "ch-01", "L")
    assert "$" not in str(error.value)


def test_a03_agotada_por_reservas(catalogo):
    # Dado: je-01 talla 32 con 2 unidades y 2 reservas activas de 1
    reservas = [_reserva("je-01", "32", 1), _reserva("je-01", "32", 1)]
    # Cuando: el cliente pregunta por je-01 en 32
    respuesta = buscar_prenda(catalogo, reservas, "je-01", "32")
    # Entonces: no hay y quedan 0 libres
    assert respuesta["hay"] is False
    assert respuesta["unidades_libres"] == 0


def test_a04_consultar_precio(catalogo):
    # Dado: go-01 con precio 0 («Consultar precio»)
    # Cuando: el cliente pregunta por la gorra
    respuesta = buscar_prenda(catalogo, [], "go-01", "UNICA")
    # Entonces: hay unidades pero no se da ningún precio
    assert respuesta["hay"] is True
    assert respuesta["precio"] is None


# ---------- HU-05: reserva ----------


def test_a05_reserva_en_efectivo(catalogo):
    # Dado: th-01 talla 41 con 3 libres a $150.000
    reservas = []
    # Cuando: Valentina Rojas reserva 2 en efectivo el 26-nov-2026 10:00
    reserva = crear_reserva(
        catalogo, reservas, "th-01", "41", 2, "efectivo", "Valentina Rojas", AHORA
    )
    # Entonces: total $300.000, vence el 27-nov-2026 10:00 y queda 1 libre
    assert reserva["total"] == 300000
    assert reserva["forma_pago"] == "efectivo"
    assert reserva["vence_en"] == datetime(2026, 11, 27, 10, 0)
    reservas.append(reserva)
    assert buscar_prenda(catalogo, reservas, "th-01", "41")["unidades_libres"] == 1


def test_a06_reserva_por_nequi(catalogo):
    # Dado: th-01 talla 41 con 3 libres a $150.000
    # Cuando: Julián Cuéllar reserva 1 y escribe « Nequi »
    reserva = crear_reserva(
        catalogo, [], "th-01", "41", 1, " Nequi ", "Julián Cuéllar", AHORA
    )
    # Entonces: forma nequi, total $150.000 y sin hora de vencimiento
    assert reserva["forma_pago"] == "nequi"
    assert reserva["total"] == 150000
    assert reserva["vence_en"] is None


def test_a07_pide_mas_de_las_libres(catalogo):
    # Dado: je-01 talla 32 con 1 unidad libre
    reservas = [_reserva("je-01", "32", 1)]
    # Cuando: un cliente intenta reservar 2
    with pytest.raises(ReservaRechazada) as error:
        crear_reserva(
            catalogo, reservas, "je-01", "32", 2, "efectivo", "Sofía Losada", AHORA
        )
    # Entonces: la rechaza y sigue quedando 1 libre
    assert "quedan 1 libres" in str(error.value)
    assert buscar_prenda(catalogo, reservas, "je-01", "32")["unidades_libres"] == 1


def test_a08_pide_justo_las_que_quedan(catalogo):
    # Dado: je-01 talla 32 con 2 unidades libres
    reservas = []
    # Cuando: un cliente reserva 2
    reserva = crear_reserva(
        catalogo, reservas, "je-01", "32", 2, "daviplata", "Andrés Charry", AHORA
    )
    reservas.append(reserva)
    # Entonces: se acepta y la prenda queda agotada
    respuesta = buscar_prenda(catalogo, reservas, "je-01", "32")
    assert respuesta["unidades_libres"] == 0
    assert respuesta["hay"] is False
    

def test_a09_mas_de_cinco_unidades(catalogo):
    # Dado: ca-01 talla M con 8 unidades libres a $70.000
    # Cuando: un cliente intenta reservar 6
    # Entonces: el sistema la rechaza por pasar el máximo de 5
    with pytest.raises(ReservaRechazada) as error:
        crear_reserva(
            catalogo, [], "ca-01", "M", 6, "efectivo", "Camilo Ramos", AHORA
        )
        assert "quedan 8 libres" in str(error.value)

def test_a10_transferencia_sin_decir_cual(catalogo):
    # Dado: th-01 en 41 con unidades
    # Cuando: el cliente escribe «transferencia»
    # Entonces: se rechaza y el motivo pide elegir una de las cuatro formas
    with pytest.raises(ReservaRechazada) as error:
        crear_reserva(
            catalogo, [], "th-01", "41", 1, "transferencia", "Laura Ospina", AHORA
        )
    motivo = str(error.value).lower()
    for forma in ("efectivo", "nequi", "daviplata", "nu"):
        assert forma in motivo


def test_a11_reserva_sin_precio(catalogo):
    # Dado: go-01 con precio 0 («Consultar precio»)
    # Cuando: un cliente intenta reservarla
    # Entonces: se rechaza porque no hay precio para calcular el total
    with pytest.raises(ReservaRechazada):
        crear_reserva(
            catalogo, [], "go-01", "UNICA", 1, "efectivo", "Diego Perdomo", AHORA
        )


def test_a12_prenda_no_disponible(catalogo):
    # Dado: bu-01 talla M marcada «NO»
    # Cuando: un cliente intenta reservar 1
    # Entonces: el sistema la rechaza
    with pytest.raises(ReservaRechazada) as error:
        crear_reserva(
            catalogo, [], "bu-01", "M", 1, "nu", "Paula Andrade", AHORA
        )
       # Hallazgo: el mensaje dice «quedan 0 libres» y no dice que la prenda no está disponible
    assert "quedan 0 libres" in str(error.value)


def test_a13_reserva_vence_a_las_24_horas(catalogo):
    # Dado: la reserva en efectivo de A-05, creada el 26-nov-2026 10:00
    reserva = crear_reserva(
        catalogo, [], "th-01", "41", 2, "efectivo", "Valentina Rojas", AHORA
    )
    # Cuando: son las 10:00 del 27-nov-2026
    ahora = AHORA + timedelta(hours=24)
    # Entonces: la reserva está vencida
    assert reserva_vencida(reserva["creada_en"], ahora) is True
    assert reserva["vence_en"] == ahora

