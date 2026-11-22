"""Fixtures compartidos de las pruebas."""

import csv
from pathlib import Path

import pytest

DATOS = Path(__file__).parent / "datos"


@pytest.fixture
def reservas_sinteticas() -> list[dict]:
    """Reservas ficticias de clientes de Neiva (ninguna persona real).

    Generadas con IA y revisadas: 15 reservas variadas y 5 casos difíciles
    (tildes y ñ, apóstrofo, cliente vacío, salto de línea y forma de pago vacía).
    La columna forma_pago_esperada se llenó a mano con la regla 2 del registro.
    """
    with open(DATOS / "reservas_sinteticas.csv", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
