"""Herramientas que el agente puede usar, y la tienda que las ejecuta.

Los datos (precio, unidades, total, vencimiento) salen siempre de las funciones
probadas de app/, nunca del modelo (RNF-03). Las reservas viven en memoria
mientras corre el servidor; Supabase queda como trabajo futuro.
"""

import json
import logging
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from app.buscar_prenda import PrendaNoEncontrada, buscar_prenda
from app.catalogo import buscar_productos, colores_de, normalizar
from app.reservar import ReservaRechazada, crear_reserva
from app.reservas import reserva_vencida

# Colombia no cambia de hora: UTC-5 todo el año.
HORA_COLOMBIA = timezone(timedelta(hours=-5), "COT")


def ahora_colombia() -> datetime:
    """Fecha y hora actual en Colombia."""
    return datetime.now(HORA_COLOMBIA)


HERRAMIENTAS = [
    {
        "name": "buscar_productos",
        "description": (
            "Busca en el catálogo de la tienda por palabras (tipo de prenda, marca, "
            "color o código). Úsala cuando el cliente pregunte qué hay o describa "
            "una prenda sin dar el código. Devuelve código, nombre, colores, tallas "
            "disponibles y precio desde."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "texto": {
                    "type": "string",
                    "description": "Palabras a buscar, por ejemplo 'tenis adidas'.",
                }
            },
            "required": ["texto"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "consultar_prenda",
        "description": (
            "Dice si hay unidades libres de una prenda en una talla y color, y su "
            "precio exacto. Úsala antes de confirmar disponibilidad o precio. Si el "
            "producto tiene varios colores y no sabes cuál quiere el cliente, "
            "devuelve los colores para que le preguntes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "codigo": {"type": "string", "description": "Código, ej. 'th-08'."},
                "talla": {"type": "string", "description": "Talla, ej. '41' o 'M'."},
                "color": {
                    "type": "string",
                    "description": "Color como sale en el catálogo; '' si no aplica.",
                },
            },
            "required": ["codigo", "talla", "color"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "crear_reserva",
        "description": (
            "Reserva una prenda para el cliente. Solo úsala cuando el cliente ya "
            "confirmó código, talla, color, cantidad (1 a 5), forma de pago "
            "(efectivo, Nequi, Daviplata o Nu) y su nombre. Si dice "
            "'transferencia', pregúntale por cuál de las tres antes de reservar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "codigo": {"type": "string"},
                "talla": {"type": "string"},
                "color": {"type": "string", "description": "'' si no aplica."},
                "cantidad": {"type": "integer"},
                "forma_pago": {"type": "string"},
                "cliente": {"type": "string", "description": "Nombre del cliente."},
            },
            "required": [
                "codigo", "talla", "color", "cantidad", "forma_pago", "cliente"
            ],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "name": "pasar_a_dueno",
        "description": (
            "Avisa al dueño para que conteste él. Úsala con quejas, descuentos, "
            "cambios, domicilios, preguntas que no son del catálogo o si el cliente "
            "pide hablar con una persona."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "motivo": {"type": "string", "description": "Resumen corto."}
            },
            "required": ["motivo"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


class Tienda:
    """Catálogo y reservas en memoria; ejecuta las herramientas del agente.

    Args:
        catalogo: filas leídas con cargar_catalogo.
        reloj: función que da la hora actual (en las pruebas, una hora fija).
        repositorio: dónde se guardan las reservas (Supabase), con guardar y
            cargar; None = solo en memoria.
    """

    def __init__(
        self,
        catalogo: list[dict],
        reloj: Callable[[], datetime] = ahora_colombia,
        repositorio=None,
    ) -> None:
        self.catalogo = catalogo
        self.reloj = reloj
        self.repositorio = repositorio
        self.reservas: list[dict] = []
        self.avisos_dueno: list[dict] = []
        if repositorio is not None:
            try:
                self.reservas = repositorio.cargar()
                logging.warning("Reservas leídas de la base: %s", len(self.reservas))
            except Exception:
                logging.exception("No se pudieron leer las reservas de la base")

    def reservas_activas(self) -> list[dict]:
        """Reservas que no han vencido (las de efectivo vencen a las 24 h)."""
        ahora = self.reloj()
        return [
            r for r in self.reservas
            if r["vence_en"] is None or not reserva_vencida(r["creada_en"], ahora)
        ]

    def _filas_del_color(self, codigo: str, color: str) -> tuple[list[dict], str]:
        """Filas de ese código y color, y el color tal como está en el catálogo.

        Raises:
            ValueError: si el producto tiene varios colores y el color no es uno.
        """
        colores = colores_de(self.catalogo, codigo)
        if not colores:
            return [f for f in self.catalogo if f["codigo"] == codigo], ""
        elegido = next((c for c in colores if normalizar(c) == normalizar(color)), None)
        if elegido is None:
            if len(colores) > 1:
                raise ValueError(
                    f"Pregunta el color. Colores de {codigo}: {', '.join(colores)}"
                )
            elegido = colores[0]
        filas = [
            f for f in self.catalogo if f["codigo"] == codigo and f["color"] == elegido
        ]
        return filas, elegido

    def _reservas_del_color(self, codigo: str, color: str) -> list[dict]:
        return [
            r for r in self.reservas_activas()
            if r["codigo"] != codigo or r.get("color", "") == color
        ]

    def consultar_prenda(self, codigo: str, talla: str, color: str) -> dict:
        """HU-01 con color: usa buscar_prenda sobre las filas de ese color."""
        filas, elegido = self._filas_del_color(codigo, color)
        prenda = buscar_prenda(
            filas, self._reservas_del_color(codigo, elegido), codigo, talla
        )
        return {"codigo": codigo, "talla": talla, "color": elegido, **prenda}

    def reservar(
        self, codigo: str, talla: str, color: str, cantidad: int,
        forma_pago: str, cliente: str, chat_id: str,
    ) -> dict:
        """HU-05 con color: usa crear_reserva y guarda la reserva en memoria."""
        filas, elegido = self._filas_del_color(codigo, color)
        reserva = crear_reserva(
            filas, self._reservas_del_color(codigo, elegido), codigo, talla,
            cantidad, forma_pago, cliente, self.reloj(),
        )
        reserva.update(
            color=elegido, chat_id=chat_id, numero=f"R-{len(self.reservas) + 1:04d}"
        )
        self.reservas.append(reserva)
        if self.repositorio is not None:
            try:
                self.repositorio.guardar(reserva)
            except Exception:
                # La reserva sigue en memoria; el dueño la ve en el panel.
                logging.exception("No se pudo guardar %s en la base", reserva["numero"])
                self.avisos_dueno.append({
                    "chat_id": chat_id,
                    "motivo": f"{reserva['numero']} no quedó guardada en la base",
                    "hora": self.reloj(),
                })
        return reserva

    def ejecutar(self, nombre: str, entrada: dict, chat_id: str) -> tuple[str, bool]:
        """Ejecuta una herramienta y devuelve (resultado en JSON, es_error)."""
        try:
            if nombre == "buscar_productos":
                resultado = {"productos": buscar_productos(self.catalogo,
                                                           entrada["texto"])}
            elif nombre == "consultar_prenda":
                resultado = self.consultar_prenda(
                    entrada["codigo"], entrada["talla"], entrada.get("color", "")
                )
            elif nombre == "crear_reserva":
                reserva = self.reservar(
                    entrada["codigo"], entrada["talla"], entrada.get("color", ""),
                    int(entrada["cantidad"]), entrada["forma_pago"],
                    entrada["cliente"], chat_id,
                )
                resultado = _reserva_para_el_modelo(reserva)
            elif nombre == "pasar_a_dueno":
                self.avisos_dueno.append(
                    {"chat_id": chat_id, "motivo": entrada["motivo"],
                     "hora": self.reloj()}
                )
                resultado = {"avisado": True}
            else:
                return f"Herramienta desconocida: {nombre}", True
        except PrendaNoEncontrada:
            return "Esa prenda (código y talla) no está en el catálogo.", True
        except (ReservaRechazada, ValueError) as motivo:
            return str(motivo), True
        except (KeyError, TypeError) as error:
            return f"Faltan datos para {nombre}: {error}", True
        return json.dumps(resultado, ensure_ascii=False), False


def _reserva_para_el_modelo(reserva: dict) -> dict:
    """La reserva con fechas en texto (sin el chat_id del cliente)."""
    vence = reserva["vence_en"]
    return {
        "numero": reserva["numero"],
        "nombre": reserva["nombre"],
        "codigo": reserva["codigo"],
        "talla": reserva["talla"],
        "color": reserva["color"],
        "cantidad": reserva["cantidad"],
        "total": reserva["total"],
        "forma_pago": reserva["forma_pago"],
        "vence_en": vence.strftime("%d-%m-%Y %I:%M %p") if vence else None,
    }
