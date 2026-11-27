"""El agente: conversa con el cliente usando Claude y las herramientas de la tienda.

Claude decide qué herramienta usar; los datos salen siempre de app/ (RNF-03).
El cliente de Claude se recibe como parámetro, así las pruebas usan uno falso
y nunca llaman a la API real ni necesitan una clave.
"""

import logging
import os
import re

import anthropic

from app.herramientas import HERRAMIENTAS, Tienda

MODELO_POR_DEFECTO = "claude-opus-5-5"
MAX_VUELTAS = 8
MAX_TOKENS = 16000
# Si Claude rechaza un mensaje por seguridad, la API lo reintenta en otro modelo.
BETA_RESPALDO = "server-side-fallback-2026-07-01"

MENSAJE_FALLA = (
    "Uy, tuve un problema técnico. Ya le aviso al equipo para que te responda."
)
MENSAJE_RECHAZO = "Eso no lo puedo responder yo; le paso tu mensaje al equipo."

INSTRUCCIONES = """\
Eres el asistente virtual de Urban, un almacén de ropa de marca para hombre (y \
algunos tenis de dama) en Neiva, Huila. Atiendes por WhatsApp en español de \
Colombia, con frases cortas, amables y sin tecnicismos. Si te preguntan, di que \
eres un asistente automático del almacén.

Datos fijos del almacén:
- Dirección: Cra. 7 # 9-2, Palermo.
- Horario: lunes a domingo de 8 a. m. a 8 p. m.; festivos de 8 a. m. a 12 m.

Reglas:
1. Precios, tallas, colores y disponibilidad salen SOLO de las herramientas. \
Nunca inventes productos ni precios. Si una herramienta no lo da, dilo.
2. Para saber qué hay, usa buscar_productos. Antes de decir que hay una talla \
o dar un precio exacto, usa consultar_prenda.
3. Si un producto tiene varios colores, pregunta cuál quiere.
4. Para reservar necesitas: prenda, talla, color, cantidad (1 a 5), forma de \
pago y nombre. Pide lo que falte, de a poco, y confirma antes de crear_reserva.
5. Formas de pago: efectivo en el almacén (la reserva dura 24 horas y luego se \
cancela) o transferencia por Nequi, Daviplata o Nu (el equipo envía los datos \
y verifica el pago). Si dicen "transferencia", pregunta por cuál de las tres.
6. No hay pasarela de pago, descuentos, domicilios ni cambios por este chat: \
para eso, para quejas o si piden una persona, usa pasar_a_dueno y dile al \
cliente que el equipo le responde pronto.
7. Si "precio" viene vacío o null, di "precio a consultar" y ofrece pasar al equipo.
8. Escribe los precios así: $130.000.
9. Escribe como en WhatsApp: texto plano, listas con guion y, si quieres \
resaltar, un solo asterisco (*Adidas Campus*). Nada de **dobles asteriscos**, \
títulos con # ni tablas.
"""


def crear_cliente_claude() -> anthropic.Anthropic:
    """Cliente real de Claude; lee ANTHROPIC_API_KEY del entorno (archivo .env)."""
    return anthropic.Anthropic()


class Agente:
    """Guarda la conversación de cada chat y responde con Claude.

    Args:
        cliente: cliente de Anthropic (o uno falso en las pruebas).
        tienda: catálogo y reservas que usan las herramientas.
        modelo: modelo de Claude; por defecto ANTHROPIC_MODEL o claude-opus-5-5.
    """

    def __init__(self, cliente, tienda: Tienda, modelo: str | None = None) -> None:
        self.cliente = cliente
        self.tienda = tienda
        self.modelo = modelo or os.getenv("ANTHROPIC_MODEL", MODELO_POR_DEFECTO)
        self.chats: dict[str, list[dict]] = {}

    def _llamar_claude(self, mensajes: list[dict]):
        return self.cliente.beta.messages.create(
            model=self.modelo,
            max_tokens=MAX_TOKENS,
            system=INSTRUCCIONES,
            tools=HERRAMIENTAS,
            messages=mensajes,
            output_config={"effort": "low"},
            betas=[BETA_RESPALDO],
            fallbacks="default",
        )

    def responder(self, chat_id: str, texto: str) -> str:
        """Agrega el mensaje del cliente al chat y devuelve la respuesta del agente.

        Args:
            chat_id: identificador del chat (en WhatsApp, el número del cliente).
            texto: lo que escribió el cliente.
        Returns:
            El texto que se le envía al cliente. Nunca lanza error: si la API
            falla, devuelve MENSAJE_FALLA y avisa al dueño.
        """
        mensajes = self.chats.setdefault(chat_id, [])
        mensajes.append({"role": "user", "content": texto.strip() or "(mensaje vacío)"})
        try:
            return self._vueltas(chat_id, mensajes)
        except anthropic.AuthenticationError:
            logging.exception("Clave de Anthropic inválida o ausente")
        except anthropic.RateLimitError:
            logging.exception("Límite de uso de la API de Anthropic")
        except anthropic.APIStatusError:
            logging.exception("La API de Anthropic devolvió un error")
        except anthropic.APIConnectionError:
            logging.exception("Sin conexión con la API de Anthropic")
        self.tienda.avisos_dueno.append(
            {"chat_id": chat_id, "motivo": "falla técnica del agente",
             "hora": self.tienda.reloj()}
        )
        # El último mensaje quedó sin respuesta; se saca para no romper el chat.
        self.chats[chat_id] = _hasta_ultima_respuesta(mensajes)
        return MENSAJE_FALLA

    def _vueltas(self, chat_id: str, mensajes: list[dict]) -> str:
        for _ in range(MAX_VUELTAS):
            respuesta = self._llamar_claude(mensajes)
            mensajes.append({"role": "assistant", "content": respuesta.content})

            if respuesta.stop_reason == "refusal":
                self.tienda.avisos_dueno.append(
                    {"chat_id": chat_id, "motivo": "mensaje rechazado por Claude",
                     "hora": self.tienda.reloj()}
                )
                return MENSAJE_RECHAZO
            if respuesta.stop_reason == "pause_turn":
                continue
            if respuesta.stop_reason != "tool_use":
                return formato_whatsapp(_texto(respuesta.content)) or MENSAJE_RECHAZO

            resultados = []
            for bloque in respuesta.content:
                if bloque.type != "tool_use":
                    continue
                contenido, es_error = self.tienda.ejecutar(
                    bloque.name, bloque.input, chat_id
                )
                resultados.append({
                    "type": "tool_result",
                    "tool_use_id": bloque.id,
                    "content": contenido,
                    "is_error": es_error,
                })
            mensajes.append({"role": "user", "content": resultados})
        logging.warning("El agente llegó a %s vueltas en %s", MAX_VUELTAS, chat_id)
        self.chats[chat_id] = _hasta_ultima_respuesta(mensajes)
        return MENSAJE_FALLA


def formato_whatsapp(texto: str) -> str:
    """Pasa el Markdown que a veces escribe Claude al formato de WhatsApp.

    Args:
        texto: respuesta del modelo, por ejemplo "## Tenis\n**Adidas Campus**".
    Returns:
        El mismo texto con **negrilla** cambiada a *negrilla* y sin los # de
        los títulos ("Tenis\n*Adidas Campus*").
    """
    texto = re.sub(r"\*\*(.+?)\*\*", r"*\1*", texto)
    return re.sub(r"(?m)^#{1,6}\s+", "", texto).strip()


def _texto(contenido) -> str:
    """Une los bloques de texto de una respuesta de Claude."""
    return "\n".join(b.text for b in contenido if b.type == "text").strip()


def _hasta_ultima_respuesta(mensajes: list[dict]) -> list[dict]:
    """Corta el chat justo después de la última respuesta de texto del agente."""
    for i in range(len(mensajes) - 1, -1, -1):
        mensaje = mensajes[i]
        if mensaje["role"] == "assistant" and not any(
            getattr(b, "type", "") == "tool_use" for b in mensaje["content"]
        ):
            return mensajes[: i + 1]
    return []
