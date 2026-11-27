"""Pruebas del agente con un cliente de Claude falso (no llama a la API)."""

import json

import anthropic
import httpx
import pytest

from app.agente import (
    BETA_RESPALDO,
    MAX_VUELTAS,
    MENSAJE_FALLA,
    MENSAJE_RECHAZO,
    MODELO_POR_DEFECTO,
    Agente,
    formato_whatsapp,
)
from app.herramientas import HERRAMIENTAS, Tienda
from tests.falsos import ClienteFalso, herramienta, respuesta, texto


@pytest.fixture
def tienda(catalogo_prueba):
    return Tienda(catalogo_prueba)


def test_respuesta_directa_sin_herramientas(tienda):
    cliente = ClienteFalso(respuesta("end_turn", texto("¡Hola! ¿Qué buscas?")))
    agente = Agente(cliente, tienda)
    assert agente.responder("573001", "hola") == "¡Hola! ¿Qué buscas?"


def test_parametros_de_la_llamada(tienda, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_MODEL", raising=False)
    cliente = ClienteFalso(respuesta("end_turn", texto("ok")))
    Agente(cliente, tienda).responder("573001", "hola")
    llamada = cliente.llamadas[0]
    assert llamada["model"] == MODELO_POR_DEFECTO
    assert llamada["tools"] is HERRAMIENTAS
    assert llamada["betas"] == [BETA_RESPALDO]
    assert llamada["fallbacks"] == "default"
    assert "Nunca inventes" in llamada["system"]
    assert llamada["messages"] == [{"role": "user", "content": "hola"}]


def test_modelo_desde_variable_de_entorno(tienda, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MODEL", "claude-haiku-5-5")
    cliente = ClienteFalso(respuesta("end_turn", texto("ok")))
    Agente(cliente, tienda).responder("573001", "hola")
    assert cliente.llamadas[0]["model"] == "claude-haiku-5-5"


def test_usa_la_herramienta_y_le_devuelve_el_resultado(tienda):
    cliente = ClienteFalso(
        respuesta("tool_use", texto("Déjame revisar."),
                  herramienta("t1", "consultar_prenda",
                              {"codigo": "je-01", "talla": "32", "color": ""})),
        respuesta("end_turn", texto("Sí hay, vale $90.000.")),
    )
    agente = Agente(cliente, tienda)
    assert agente.responder("573001", "¿hay jean 32?") == "Sí hay, vale $90.000."

    resultado = cliente.llamadas[1]["messages"][-1]["content"][0]
    assert resultado["tool_use_id"] == "t1"
    assert resultado["is_error"] is False
    assert json.loads(resultado["content"])["precio"] == 90000


def test_reserva_completa_queda_guardada(tienda):
    entrada = {"codigo": "je-01", "talla": "32", "color": "", "cantidad": 1,
               "forma_pago": "Daviplata", "cliente": "Julián Cuéllar"}
    cliente = ClienteFalso(
        respuesta("tool_use", herramienta("t1", "crear_reserva", entrada)),
        respuesta("end_turn", texto("Listo, reserva R-0001.")),
    )
    Agente(cliente, tienda).responder("573002", "sí, resérvalo")
    assert tienda.reservas[0]["forma_pago"] == "daviplata"
    assert tienda.reservas[0]["chat_id"] == "573002"


def test_error_de_herramienta_va_marcado(tienda):
    cliente = ClienteFalso(
        respuesta("tool_use", herramienta("t1", "consultar_prenda",
                                          {"codigo": "zz", "talla": "1", "color": ""})),
        respuesta("end_turn", texto("Esa no la tenemos.")),
    )
    Agente(cliente, tienda).responder("573001", "¿tienen zz?")
    resultado = cliente.llamadas[1]["messages"][-1]["content"][0]
    assert resultado["is_error"] is True


def test_varias_herramientas_en_un_turno_van_en_un_solo_mensaje(tienda):
    cliente = ClienteFalso(
        respuesta("tool_use",
                  herramienta("a", "buscar_productos", {"texto": "jean"}),
                  herramienta("b", "buscar_productos", {"texto": "gorra"})),
        respuesta("end_turn", texto("Tenemos jeans y gorras.")),
    )
    Agente(cliente, tienda).responder("573001", "jeans y gorras")
    ultimo = cliente.llamadas[1]["messages"][-1]
    assert [r["tool_use_id"] for r in ultimo["content"]] == ["a", "b"]


def test_cada_chat_tiene_su_propia_conversacion(tienda):
    cliente = ClienteFalso(*(respuesta("end_turn", texto("ok")) for _ in range(3)))
    agente = Agente(cliente, tienda)
    agente.responder("A", "uno")
    agente.responder("B", "otro")
    agente.responder("A", "dos")
    assert len(cliente.llamadas[2]["messages"]) == 3
    assert len(agente.chats["B"]) == 2


def test_mensaje_vacio(tienda):
    cliente = ClienteFalso(respuesta("end_turn", texto("¿Me repites?")))
    Agente(cliente, tienda).responder("A", "   ")
    assert cliente.llamadas[0]["messages"][0]["content"] == "(mensaje vacío)"


def test_rechazo_pasa_al_dueno(tienda):
    cliente = ClienteFalso(respuesta("refusal"))
    assert Agente(cliente, tienda).responder("A", "...") == MENSAJE_RECHAZO
    assert tienda.avisos_dueno[0]["motivo"] == "mensaje rechazado por Claude"


def test_respuesta_sin_texto(tienda):
    cliente = ClienteFalso(respuesta("end_turn"))
    assert Agente(cliente, tienda).responder("A", "hola") == MENSAJE_RECHAZO


def test_pause_turn_sigue(tienda):
    cliente = ClienteFalso(respuesta("pause_turn"),
                           respuesta("end_turn", texto("listo")))
    assert Agente(cliente, tienda).responder("A", "hola") == "listo"


def test_tope_de_vueltas(tienda):
    bucle = [respuesta("tool_use", herramienta(f"t{i}", "buscar_productos",
                                               {"texto": "jean"}))
             for i in range(MAX_VUELTAS)]
    cliente = ClienteFalso(*bucle)
    agente = Agente(cliente, tienda)
    assert agente.responder("A", "hola") == MENSAJE_FALLA
    assert agente.chats["A"] == []


def _error_api(clase, codigo):
    peticion = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return clase("falla", response=httpx.Response(codigo, request=peticion), body=None)


@pytest.mark.parametrize("error", [
    _error_api(anthropic.AuthenticationError, 401),
    _error_api(anthropic.RateLimitError, 429),
    _error_api(anthropic.InternalServerError, 500),
    anthropic.APIConnectionError(
        request=httpx.Request("POST", "https://api.anthropic.com")),
])
def test_fallas_de_la_api_no_tumban_el_chat(tienda, error):
    cliente = ClienteFalso(respuesta("end_turn", texto("hola")), error)
    agente = Agente(cliente, tienda)
    agente.responder("A", "hola")
    assert agente.responder("A", "¿hay jeans?") == MENSAJE_FALLA
    assert tienda.avisos_dueno[-1]["motivo"] == "falla técnica del agente"
    # Se quita el mensaje que quedó sin respuesta: queda el primer intercambio.
    assert len(agente.chats["A"]) == 2


@pytest.mark.parametrize("entrada, esperado", [
    ("**Adidas Campus** a $130.000", "*Adidas Campus* a $130.000"),
    ("## Tenis\n- **th-08** y **th-07**", "Tenis\n- *th-08* y *th-07*"),
    ("Sin formato", "Sin formato"),
    ("*Ya en WhatsApp*", "*Ya en WhatsApp*"),
    ("Precio 2 ** 3 sin cerrar", "Precio 2 ** 3 sin cerrar"),
])
def test_formato_whatsapp(entrada, esperado):
    assert formato_whatsapp(entrada) == esperado


def test_la_respuesta_sale_en_formato_whatsapp(tienda):
    cliente = ClienteFalso(respuesta("end_turn", texto("Tenemos **Adidas Campus**")))
    assert Agente(cliente, tienda).responder("A", "hola") == "Tenemos *Adidas Campus*"
    assert "un solo asterisco" in cliente.llamadas[0]["system"]
