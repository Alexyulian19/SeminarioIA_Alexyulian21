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


@pytest.fixture
def catalogo_prueba() -> list[dict]:
    """Catálogo pequeño con las columnas de la web (datos de prueba).

    th-08 tiene dos colores; je-01 tiene cantidad 2; go-01 no tiene precio;
    bu-01 está marcado NO. La cantidad vacía se toma como 5.
    """
    from app.catalogo import cargar_catalogo

    return cargar_catalogo(DATOS / "catalogo_prueba.csv")
