"""Servidor FastAPI: chat local tipo WhatsApp y webhook de la WhatsApp Cloud API.

Correr en local (desde la raíz del proyecto, con el .env lleno):
    uvicorn app.servidor:crear_app --factory --reload
y abrir http://127.0.0.1:8000 en el navegador.
"""

import hashlib
import hmac
import json
import logging
import os
from collections.abc import Callable
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.agente import Agente, crear_cliente_claude
from app.catalogo import cargar_catalogo
from app.herramientas import Tienda

RAIZ = Path(__file__).resolve().parent.parent
PAGINA_CHAT = Path(__file__).parent / "web" / "chat.html"
CATALOGO_POR_DEFECTO = RAIZ / "datos" / "catalogo.csv"
VERSION_GRAPH = "v23.0"


class MensajeChat(BaseModel):
    """Mensaje que manda la página del chat local."""

    chat_id: str = Field(min_length=1, max_length=40)
    texto: str = Field(min_length=1, max_length=1000)


def firma_valida(cuerpo: bytes, firma: str | None, secreto: str) -> bool:
    """Revisa la cabecera X-Hub-Signature-256 que pone Meta en cada aviso.

    Args:
        cuerpo: bytes exactos del cuerpo recibido.
        firma: valor de la cabecera, "sha256=<hex>", o None si no vino.
        secreto: App Secret de la app de Meta.
    Returns:
        True si la firma coincide con el HMAC-SHA256 del cuerpo.
    """
    if not firma or not firma.startswith("sha256="):
        return False
    esperada = hmac.new(secreto.encode(), cuerpo, hashlib.sha256).hexdigest()
    return hmac.compare_digest(esperada, firma.removeprefix("sha256="))


def mensajes_de_texto(aviso: dict) -> list[dict]:
    """Saca los mensajes de texto de un aviso del webhook de WhatsApp.

    Returns:
        Lista de {"id", "de", "texto"}; ignora estados, imágenes, audios, etc.
    """
    encontrados = []
    for entrada in aviso.get("entry", []):
        for cambio in entrada.get("changes", []):
            for mensaje in cambio.get("value", {}).get("messages", []):
                if mensaje.get("type") == "text":
                    encontrados.append({
                        "id": mensaje.get("id", ""),
                        "de": mensaje.get("from", ""),
                        "texto": mensaje.get("text", {}).get("body", ""),
                    })
    return encontrados


def errores_de_entrega(aviso: dict) -> list[str]:
    """Saca los errores de los avisos de estado (mensajes que Meta no entregó).

    Returns:
        Lista de textos "codigo: titulo" de cada estado "failed".
    """
    errores = []
    for entrada in aviso.get("entry", []):
        for cambio in entrada.get("changes", []):
            for estado in cambio.get("value", {}).get("statuses", []):
                if estado.get("status") == "failed":
                    for error in estado.get("errors", []) or [{}]:
                        errores.append(
                            f"{error.get('code', '?')}: "
                            f"{error.get('title') or error.get('message', '')}"
                        )
    return errores


def crear_enviador(token: str, phone_number_id: str) -> Callable[[str, str], None]:
    """Función que envía un texto por la WhatsApp Cloud API."""
    url = f"https://graph.facebook.com/{VERSION_GRAPH}/{phone_number_id}/messages"

    def enviar(numero: str, texto: str) -> None:
        respuesta = httpx.post(
            url,
            headers={"Authorization": f"Bearer {token}"},
            json={
                "messaging_product": "whatsapp",
                "to": numero,
                "type": "text",
                "text": {"body": texto},
            },
            timeout=20,
        )
        if respuesta.status_code >= 400:
            logging.error("WhatsApp no aceptó el mensaje: %s", respuesta.text)
        else:
            logging.warning("Respuesta enviada a ...%s", numero[-4:])

    return enviar


def crear_app(
    agente: Agente | None = None,
    enviar: Callable[[str, str], None] | None = None,
    verify_token: str | None = None,
    app_secret: str | None = None,
) -> FastAPI:
    """Arma la aplicación. Sin argumentos, lee todo del .env (uso real).

    Args:
        agente: agente ya armado (las pruebas pasan uno con Claude falso).
        enviar: función (numero, texto) que responde por WhatsApp; None = no envía.
        verify_token: WHATSAPP_VERIFY_TOKEN para verificar el webhook.
        app_secret: WHATSAPP_APP_SECRET para revisar la firma; None = no revisa.
    """
    if agente is None:
        load_dotenv(RAIZ / ".env")
        catalogo = cargar_catalogo(os.getenv("CATALOGO_CSV") or CATALOGO_POR_DEFECTO)
        agente = Agente(crear_cliente_claude(), Tienda(catalogo))
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
        app_secret = os.getenv("WHATSAPP_APP_SECRET")
        token = os.getenv("WHATSAPP_TOKEN")
        phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        if token and phone_id:
            enviar = crear_enviador(token, phone_id)

    app = FastAPI(title="Agente de WhatsApp de Urban")
    vistos: set[str] = set()

    @app.get("/")
    def pagina_chat() -> FileResponse:
        return FileResponse(PAGINA_CHAT)

    @app.post("/api/chat")
    def chat_local(mensaje: MensajeChat) -> dict:
        return {"respuesta": agente.responder(mensaje.chat_id, mensaje.texto)}

    @app.get("/api/reservas")
    def ver_reservas() -> dict:
        activas = agente.tienda.reservas_activas()
        return {
            "reservas": [
                {**r, "creada_en": r["creada_en"].isoformat(),
                 "vence_en": r["vence_en"].isoformat() if r["vence_en"] else None}
                for r in activas
            ],
            "avisos_dueno": [
                {**a, "hora": a["hora"].isoformat()} for a in agente.tienda.avisos_dueno
            ],
        }

    @app.get("/webhook")
    def verificar_webhook(
        modo: str = Query("", alias="hub.mode"),
        token: str = Query("", alias="hub.verify_token"),
        reto: str = Query("", alias="hub.challenge"),
    ) -> PlainTextResponse:
        if verify_token and modo == "subscribe" and hmac.compare_digest(
            token, verify_token
        ):
            return PlainTextResponse(reto)
        raise HTTPException(status_code=403, detail="Token de verificación inválido")

    @app.post("/webhook")
    async def recibir_webhook(request: Request) -> dict:
        cuerpo = await request.body()
        if app_secret and not firma_valida(
            cuerpo, request.headers.get("X-Hub-Signature-256"), app_secret
        ):
            raise HTTPException(status_code=401, detail="Firma inválida")
        try:
            aviso = json.loads(cuerpo or b"{}")
        except json.JSONDecodeError as error:
            raise HTTPException(status_code=400, detail="JSON inválido") from error
        for error in errores_de_entrega(aviso):
            logging.error("WhatsApp no pudo entregar la respuesta: %s", error)
        mensajes = mensajes_de_texto(aviso)
        if not mensajes and not aviso.get("entry"):
            logging.warning("Aviso de WhatsApp sin mensajes: %s", cuerpo[:300])
        for mensaje in mensajes:
            logging.warning("Mensaje de ...%s: %s", mensaje["de"][-4:],
                            mensaje["texto"][:60])
            if mensaje["id"] in vistos:
                continue  # Meta reenvía el mismo aviso si tardamos en contestar.
            vistos.add(mensaje["id"])
            respuesta = await run_in_threadpool(
                agente.responder, mensaje["de"], mensaje["texto"]
            )
            if enviar:
                await run_in_threadpool(enviar, mensaje["de"], respuesta)
        return {"ok": True}

    return app
