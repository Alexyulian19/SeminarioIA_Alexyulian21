"""Guardar y leer las reservas en PostgreSQL de Supabase (por su API REST).

Sigue el modelo ER de la semana 4 (RESERVA y LINEA_RESERVA). La reserva y su
línea se guardan en una sola transacción con la función guardar_reserva
(docs/supabase/crear_tablas.sql). Si no hay SUPABASE_URL y SUPABASE_KEY, la
tienda sigue con las reservas en memoria.
"""

from datetime import datetime

import httpx

from app.herramientas import HORA_COLOMBIA

COLUMNAS = (
    "numero,chat_id,nombre_cliente,forma_pago,total,creada_en,vence_en,"
    "linea_reserva(codigo,color,talla,nombre_prenda,cantidad)"
)


class RepositorioSupabase:
    """Reservas en Supabase.

    Args:
        url: SUPABASE_URL, por ejemplo https://abcd.supabase.co
        clave: SUPABASE_KEY (clave secreta / service_role; solo en el servidor).
        http: cliente con .get y .post (httpx; en las pruebas, uno falso).
    """

    def __init__(self, url: str, clave: str, http=httpx) -> None:
        self.base = url.rstrip("/") + "/rest/v1"
        self.http = http
        self.cabeceras = {"apikey": clave, "Content-Type": "application/json"}
        # Las claves nuevas (sb_secret_...) van solo en apikey; las antiguas
        # (JWT de service_role) también van como Bearer.
        if not clave.startswith("sb_"):
            self.cabeceras["Authorization"] = f"Bearer {clave}"

    def guardar(self, reserva: dict) -> None:
        """Guarda la reserva y su línea en una transacción.

        Raises:
            httpx.HTTPStatusError: si Supabase responde con error.
            httpx.HTTPError: si no hay conexión.
        """
        vence = reserva["vence_en"]
        datos = {
            "numero": reserva["numero"],
            "chat_id": reserva["chat_id"],
            "nombre_cliente": reserva["cliente"],
            "forma_pago": reserva["forma_pago"],
            "total": reserva["total"],
            "creada_en": reserva["creada_en"].isoformat(),
            "vence_en": vence.isoformat() if vence else None,
            "codigo": reserva["codigo"],
            "color": reserva["color"],
            "talla": reserva["talla"],
            "nombre_prenda": reserva["nombre"],
            "cantidad": reserva["cantidad"],
            "precio_unitario": reserva["total"] // reserva["cantidad"],
        }
        respuesta = self.http.post(
            f"{self.base}/rpc/guardar_reserva",
            headers=self.cabeceras, json={"datos": datos}, timeout=15,
        )
        respuesta.raise_for_status()

    def cargar(self) -> list[dict]:
        """Lee todas las reservas guardadas, con el formato que usa la tienda."""
        respuesta = self.http.get(
            f"{self.base}/reserva",
            headers=self.cabeceras,
            params={"select": COLUMNAS, "order": "id.asc"},
            timeout=15,
        )
        respuesta.raise_for_status()
        return [_reserva_de_fila(fila) for fila in respuesta.json()]


def _fecha(texto: str | None) -> datetime | None:
    if not texto:
        return None
    return datetime.fromisoformat(texto).astimezone(HORA_COLOMBIA)


def _reserva_de_fila(fila: dict) -> dict:
    """Convierte una fila de Supabase (con su línea) en una reserva de la tienda."""
    linea = (fila.get("linea_reserva") or [{}])[0]
    return {
        "numero": fila["numero"],
        "chat_id": fila["chat_id"],
        "cliente": fila["nombre_cliente"],
        "forma_pago": fila["forma_pago"],
        "total": fila["total"],
        "creada_en": _fecha(fila["creada_en"]),
        "vence_en": _fecha(fila.get("vence_en")),
        "codigo": linea.get("codigo", ""),
        "color": linea.get("color", ""),
        "talla": linea.get("talla", ""),
        "nombre": linea.get("nombre_prenda", ""),
        "cantidad": linea.get("cantidad", 0),
    }
