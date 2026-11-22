"""Pruebas de app/reservas.py.

Los esperados son fijos y salen de las reglas de registro_pruebas.md, sección 1.
Los ids de cada fila (R1-1, D2...) son los de las tablas de casos.
"""

import re
from datetime import datetime

import pytest

from app.reservas import (
    calcular_total,
    normalizar_forma_pago,
    puede_reservar,
    reserva_vencida,
)


def dt(dia, hora, minuto=0, segundo=0):
    """Fecha de noviembre de 2026 (misma zona para todas)."""
    return datetime(2026, 11, dia, hora, minuto, segundo)


# ---------- Regla 1: reserva_vencida ----------

@pytest.mark.parametrize(
    "creada_en, ahora, esperado",
    [
        (dt(21, 10), dt(21, 12), False),  # R1-1 partición válida: no vencida (2 h)
        (dt(21, 10), dt(22, 16), True),  # R1-2 partición válida: vencida (30 h)
        (dt(21, 10), dt(21, 10), False),  # R1-3 límite: recién creada (0 s)
        (dt(21, 10), dt(22, 9, 59, 59), False),  # R1-4 límite: 1 s antes de vencer
        (dt(21, 10), dt(22, 10, 0, 0), True),  # R1-5 límite: 24 h exactas
        (dt(21, 10), dt(22, 10, 0, 1), True),  # R1-6 límite: 1 s después de 24 h
    ],
    ids=["R1-1", "R1-2", "R1-3", "R1-4", "R1-5", "R1-6"],
)
def test_reserva_vencida(creada_en, ahora, esperado):
    assert reserva_vencida(creada_en, ahora) is esperado


@pytest.mark.parametrize(
    "creada_en, ahora",
    [
        (dt(21, 10), dt(21, 9)),  # R1-7 partición inválida: ahora antes de creada_en
        (dt(21, 10), dt(21, 9, 59, 59)),  # R1-8 límite inválido: un segundo antes
    ],
    ids=["R1-7", "R1-8"],
)
def test_reserva_vencida_ahora_anterior_lanza_error(creada_en, ahora):
    with pytest.raises(ValueError):
        reserva_vencida(creada_en, ahora)


# ---------- Regla 2: normalizar_forma_pago ----------

@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("efectivo", "efectivo"),  # R2-1 partición válida: efectivo
        ("nequi", "nequi"),  # R2-2 partición válida: nequi
        ("daviplata", "daviplata"),  # R2-3 partición válida: daviplata
        ("nu", "nu"),  # R2-4 partición válida: nu
        ("NEQUI", "nequi"),  # R2-5 partición válida: mayúsculas
        ("Daviplata", "daviplata"),  # R2-6 partición válida: mayúscula inicial
        ("  efectivo ", "efectivo"),  # R2-7 partición válida: espacios a los lados
        ("nequi\n", "nequi"),  # R2-13 partición válida: salto de línea al final
    ],
    ids=["R2-1", "R2-2", "R2-3", "R2-4", "R2-5", "R2-6", "R2-7", "R2-13"],
)
def test_normalizar_forma_pago(texto, esperado):
    assert normalizar_forma_pago(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "bancolombia",  # R2-8 partición inválida: banco no aceptado
        "transferencia",  # R2-9 partición inválida: transferencia sin decir cuál
        "Nu Bank",  # R2-10 partición inválida: nombre con más palabras
        "",  # R2-11 límite texto vacío: vacío
        "   ",  # R2-12 límite texto vacío: solo espacios
        "Nequí",  # R2-14 partición inválida: con tilde (decisión de Alex)
    ],
    ids=["R2-8", "R2-9", "R2-10", "R2-11", "R2-12", "R2-14"],
)
def test_normalizar_forma_pago_invalida_lanza_error(texto):
    with pytest.raises(ValueError):
        normalizar_forma_pago(texto)


# ---------- Regla 3: calcular_total ----------

@pytest.mark.parametrize(
    "precio, cantidad, esperado",
    [
        (80_000, 2, 160_000),  # R3-1 partición válida: precio y cantidad normales
        (40_000, 1, 40_000),  # R3-2 límite: precio mínimo
        (150_000, 1, 150_000),  # R3-4 límite: cantidad mínima
        (150_000, 5, 750_000),  # R3-5 límite: cantidad máxima
    ],
    ids=["R3-1", "R3-2", "R3-4", "R3-5"],
)
def test_calcular_total(precio, cantidad, esperado):
    assert calcular_total(precio, cantidad) == esperado


@pytest.mark.parametrize(
    "precio, cantidad",
    [
        (39_999, 1),  # R3-3 límite: un peso menos que el mínimo
        (150_000, 6),  # R3-6 límite: una más que el máximo
        (150_000, 0),  # R3-7 límite: cantidad cero
        (150_000, -1),  # R3-8 partición inválida: cantidad negativa
        (None, 1),  # R3-9 partición inválida: «Consultar precio»
        (0, 1),  # R3-10 partición inválida: precio 0
    ],
    ids=["R3-3", "R3-6", "R3-7", "R3-8", "R3-9", "R3-10"],
)
def test_calcular_total_invalido_lanza_error(precio, cantidad):
    with pytest.raises(ValueError):
        calcular_total(precio, cantidad)


# ---------- Regla 4: puede_reservar ----------

@pytest.mark.parametrize(
    "disponible, libres, cantidad, esperado",
    [
        ("SI", 3, 3, True),  # R4-1 límite: pide exactamente las que quedan
        ("SI", 3, 1, True),  # R4-3 límite: cantidad mínima
        ("SI", 3, 0, False),  # R4-4 límite: cantidad cero
        ("SI", 8, 5, True),  # R4-5 límite: cantidad máxima con stock
        ("SI", 0, 1, False),  # R4-7 límite: agotada (0 libres)
        ("si", 3, 1, False),  # R4-8 partición inválida: disponible en minúscula
    ],
    ids=["R4-1", "R4-3", "R4-4", "R4-5", "R4-7", "R4-8"],
)
def test_puede_reservar_casos_de_limite(disponible, libres, cantidad, esperado):
    assert puede_reservar(disponible, libres, cantidad) is esperado


@pytest.mark.parametrize(
    "disponible, libres, cantidad, esperado",
    [
        ("SI", 3, 2, True),  # D1: las tres condiciones se cumplen
        ("SI", 3, 4, False),  # D2: solo falla C3, en el borde (una más que las libres)
        ("SI", 8, 6, False),  # D3: solo falla C2, en el borde (una más que el máximo)
        ("NO", 3, 2, False),  # D5: solo falla C1 (D6 a D8 no importan si C1 es No)
    ],
    ids=["D1", "D2", "D3", "D5"],
)
def test_puede_reservar_tabla_de_decision(disponible, libres, cantidad, esperado):
    assert puede_reservar(disponible, libres, cantidad) is esperado


def test_puede_reservar_libres_negativo_lanza_error():
    # R4-9 partición inválida: unidades libres negativas
    with pytest.raises(ValueError):
        puede_reservar("SI", -1, 1)


# ---------- Datos sintéticos (fixture reservas_sinteticas) ----------

def test_datos_sinteticos_son_ficticios(reservas_sinteticas):
    # 20 reservas, todas con teléfono del patrón ficticio 300 000 xxxx
    assert len(reservas_sinteticas) == 20
    for fila in reservas_sinteticas:
        assert re.fullmatch(r"300 000 \d{4}", fila["telefono"]), fila["telefono"]


def test_forma_de_pago_de_las_reservas_sinteticas(reservas_sinteticas):
    # Cada fila trae la forma de pago como la escribió el cliente y el
    # esperado que salió de la regla 2 (ERROR = ValueError).
    for fila in reservas_sinteticas:
        if fila["forma_pago_esperada"] == "ERROR":
            with pytest.raises(ValueError):
                normalizar_forma_pago(fila["forma_pago_escrita"])
        else:
            esperado = fila["forma_pago_esperada"]
            assert normalizar_forma_pago(fila["forma_pago_escrita"]) == esperado
