"""Chat con el agente en la terminal (sin navegador ni WhatsApp).

Uso, desde la raíz del proyecto y con el .env lleno:  python -m app.consola
Escribe "salir" para terminar.
"""

import os

from dotenv import load_dotenv

from app.agente import Agente, crear_cliente_claude
from app.catalogo import cargar_catalogo
from app.herramientas import Tienda
from app.servidor import CATALOGO_POR_DEFECTO, RAIZ


def conversar(agente: Agente, leer=input, escribir=print) -> None:
    """Lee mensajes hasta "salir" y escribe la respuesta del agente."""
    escribir("Chat de prueba de Urban. Escribe 'salir' para terminar.")
    while True:
        try:
            texto = leer("Tú: ").strip()
        except EOFError:
            break
        if texto.lower() == "salir":
            break
        if texto:
            escribir("Agente: " + agente.responder("consola", texto))


def main() -> None:  # pragma: no cover - usa la API real
    load_dotenv(RAIZ / ".env")
    catalogo = cargar_catalogo(os.getenv("CATALOGO_CSV") or CATALOGO_POR_DEFECTO)
    conversar(Agente(crear_cliente_claude(), Tienda(catalogo)))


if __name__ == "__main__":  # pragma: no cover
    main()
