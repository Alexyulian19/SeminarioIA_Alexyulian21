"""Pruebas del servidor FastAPI: chat local y webhook de WhatsApp."""

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app import servidor
from app.agente import Agente
from app.herramientas import Tienda
from tests.falsos import ClienteFalso, respuesta, texto

SECRETO = "secreto-de-prueba"
CLAVE_PANEL = "clave-panel-prueba"


def aviso_de_texto(id_: str, de: str, cuerpo: str) -> dict:
    """Aviso como lo manda Meta (recortado a lo que se usa)."""
    return {"entry": [{"changes": [{"value": {"messages": [
        {"id": id_, "from": de, "type": "text", "text": {"body": cuerpo}},
        {"id": id_ + "img", "from": de, "type": "image"},
    ]}}]}]}


def firmar(cuerpo: bytes) -> str:
    return "sha256=" + hmac.new(SECRETO.encode(), cuerpo, hashlib.sha256).hexdigest()


@pytest.fixture(autouse=True)
def sin_supabase(monkeypatch):
    """Las pruebas nunca usan la base real, aunque el .env tenga las claves."""
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_KEY", "")


@pytest.fixture
def armado(catalogo_prueba):
    cliente = ClienteFalso(*(respuesta("end_turn", texto("Hola, soy Urban"))
                             for _ in range(5)))
    agente = Agente(cliente, Tienda(catalogo_prueba))
    enviados: list[tuple[str, str]] = []
    app = servidor.crear_app(agente, lambda n, t: enviados.append((n, t)),
                             verify_token="mi-token",  # noqa: S106 (dato de prueba)
                             app_secret=SECRETO, panel_clave=CLAVE_PANEL)
    return TestClient(app), cliente, agente, enviados


def test_pagina_del_chat(armado):
    http, *_ = armado
    pagina = http.get("/")
    assert pagina.status_code == 200
    assert "Urban" in pagina.text


def test_chat_local(armado):
    http, cliente, *_ = armado
    r = http.post("/api/chat", json={"chat_id": "web-1", "texto": "hola"})
    assert r.json() == {"respuesta": "Hola, soy Urban"}
    assert len(cliente.llamadas) == 1


def test_chat_local_rechaza_texto_vacio(armado):
    http, *_ = armado
    assert http.post("/api/chat", json={"chat_id": "w", "texto": ""}).status_code == 422


def test_panel_de_reservas(armado):
    http, _, agente, _ = armado
    agente.tienda.ejecutar("crear_reserva", {
        "codigo": "je-01", "talla": "32", "color": "", "cantidad": 1,
        "forma_pago": "efectivo", "cliente": "Valentina Rojas"}, "web-1")
    agente.tienda.ejecutar("pasar_a_dueno", {"motivo": "queja"}, "web-1")
    datos = http.get("/api/reservas", headers={"X-Clave-Panel": CLAVE_PANEL}).json()
    assert datos["reservas"][0]["numero"] == "R-0001"
    assert datos["reservas"][0]["vence_en"].endswith("-05:00")
    assert datos["avisos_dueno"][0]["motivo"] == "queja"


def test_verificar_webhook(armado):
    http, *_ = armado
    r = http.get("/webhook", params={"hub.mode": "subscribe",
                                     "hub.verify_token": "mi-token",
                                     "hub.challenge": "12345"})
    assert r.status_code == 200
    assert r.text == "12345"


def test_verificar_webhook_con_token_malo(armado):
    http, *_ = armado
    r = http.get("/webhook", params={"hub.mode": "subscribe",
                                     "hub.verify_token": "otro",
                                     "hub.challenge": "12345"})
    assert r.status_code == 403


def test_webhook_responde_por_whatsapp(armado):
    http, _, _, enviados = armado
    cuerpo = json.dumps(aviso_de_texto("wamid.1", "573001112233", "hola")).encode()
    r = http.post("/webhook", content=cuerpo,
                  headers={"X-Hub-Signature-256": firmar(cuerpo)})
    assert r.status_code == 200
    assert enviados == [("573001112233", "Hola, soy Urban")]


def test_webhook_ignora_mensaje_repetido(armado):
    http, cliente, _, enviados = armado
    cuerpo = json.dumps(aviso_de_texto("wamid.1", "573001112233", "hola")).encode()
    for _ in range(2):
        http.post("/webhook", content=cuerpo,
                  headers={"X-Hub-Signature-256": firmar(cuerpo)})
    assert len(enviados) == 1
    assert len(cliente.llamadas) == 1


def test_webhook_sin_firma_se_rechaza(armado):
    http, _, _, enviados = armado
    cuerpo = json.dumps(aviso_de_texto("wamid.2", "573", "hola")).encode()
    assert http.post("/webhook", content=cuerpo).status_code == 401
    r = http.post("/webhook", content=cuerpo,
                  headers={"X-Hub-Signature-256": "sha256=000"})
    assert r.status_code == 401
    assert enviados == []


def test_webhook_json_invalido(armado):
    http, *_ = armado
    cuerpo = b"{no es json"
    r = http.post("/webhook", content=cuerpo,
                  headers={"X-Hub-Signature-256": firmar(cuerpo)})
    assert r.status_code == 400


def test_webhook_de_estado_no_responde(armado):
    http, cliente, _, enviados = armado
    cuerpo = json.dumps({"entry": [{"changes": [{"value": {"statuses": []}}]}]})
    r = http.post("/webhook", content=cuerpo.encode(),
                  headers={"X-Hub-Signature-256": firmar(cuerpo.encode())})
    assert r.status_code == 200
    assert enviados == [] and cliente.llamadas == []


def test_sin_enviador_igual_responde_200(catalogo_prueba):
    cliente = ClienteFalso(respuesta("end_turn", texto("ok")))
    app = servidor.crear_app(Agente(cliente, Tienda(catalogo_prueba)))
    cuerpo = json.dumps(aviso_de_texto("w9", "573", "hola"))
    assert TestClient(app).post("/webhook", content=cuerpo).status_code == 200
    assert len(cliente.llamadas) == 1


def test_crear_app_desde_el_entorno(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-falsa-de-prueba")
    monkeypatch.setenv("WHATSAPP_TOKEN", "token-falso")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123")
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "v")
    monkeypatch.delenv("CATALOGO_CSV", raising=False)
    app = servidor.crear_app()
    r = TestClient(app).get("/webhook", params={"hub.mode": "subscribe",
                                                "hub.verify_token": "v",
                                                "hub.challenge": "ok"})
    assert r.text == "ok"


@pytest.mark.parametrize("codigo", [200, 400])
def test_enviador_llama_a_la_api_de_meta(monkeypatch, caplog, codigo):
    llamadas = []

    class Respuesta:
        status_code = codigo
        text = "error de prueba"

    def post_falso(url, **opciones):
        llamadas.append((url, opciones))
        return Respuesta()

    monkeypatch.setattr(servidor.httpx, "post", post_falso)
    servidor.crear_enviador("tok", "999")("573001", "hola")
    url, opciones = llamadas[0]
    assert url.endswith("/999/messages")
    assert opciones["headers"]["Authorization"] == "Bearer tok"
    assert opciones["json"]["to"] == "573001"
    assert ("error de prueba" in caplog.text) == (codigo == 400)


def test_crear_app_sin_whatsapp_configurado(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-falsa-de-prueba")
    monkeypatch.setenv("WHATSAPP_TOKEN", "")
    assert TestClient(servidor.crear_app()).get("/").status_code == 200


def test_consola(catalogo_prueba):
    from app.consola import conversar

    cliente = ClienteFalso(respuesta("end_turn", texto("Hola")))
    entradas = iter(["hola", "", "salir"])
    salida: list[str] = []
    conversar(Agente(cliente, Tienda(catalogo_prueba)),
              lambda _: next(entradas), salida.append)
    assert salida[-1] == "Agente: Hola"


def test_consola_termina_con_fin_de_archivo(catalogo_prueba):
    from app.consola import conversar

    def leer(_):
        raise EOFError

    salida: list[str] = []
    conversar(Agente(ClienteFalso(), Tienda(catalogo_prueba)), leer, salida.append)
    assert len(salida) == 1


def test_estado_fallido_queda_en_el_registro(armado, caplog):
    http, *_ = armado
    aviso = {"entry": [{"changes": [{"value": {"statuses": [
        {"status": "failed", "errors": [{"code": 131026, "title": "No entregado"}]},
        {"status": "failed"},
        {"status": "delivered"},
    ]}}]}]}
    cuerpo = json.dumps(aviso).encode()
    http.post("/webhook", content=cuerpo,
              headers={"X-Hub-Signature-256": firmar(cuerpo)})
    assert "131026: No entregado" in caplog.text
    assert "?: " in caplog.text


def test_aviso_vacio_queda_en_el_registro(armado, caplog):
    http, *_ = armado
    cuerpo = b"{}"
    http.post("/webhook", content=cuerpo,
              headers={"X-Hub-Signature-256": firmar(cuerpo)})
    assert "sin mensajes" in caplog.text


@pytest.mark.parametrize("cabeceras", [{}, {"X-Clave-Panel": "otra"}])
def test_panel_sin_clave_correcta_se_rechaza(armado, cabeceras):
    http, *_ = armado
    assert http.get("/api/reservas", headers=cabeceras).status_code == 403


def test_panel_apagado_si_no_hay_clave_configurada(catalogo_prueba):
    app = servidor.crear_app(Agente(ClienteFalso(), Tienda(catalogo_prueba)))
    r = TestClient(app).get("/api/reservas", headers={"X-Clave-Panel": ""})
    assert r.status_code == 403


def test_limite_por_chat(catalogo_prueba):
    cliente = ClienteFalso(*(respuesta("end_turn", texto("ok")) for _ in range(3)))
    app = servidor.crear_app(Agente(cliente, Tienda(catalogo_prueba)),
                             limitador=servidor.Limitador(2, 100))
    http = TestClient(app)
    textos = [http.post("/api/chat", json={"chat_id": "a", "texto": "hola"}).json()
              for _ in range(3)]
    assert textos[-1]["respuesta"] == servidor.MENSAJE_LIMITE
    assert len(cliente.llamadas) == 2
    otro = http.post("/api/chat", json={"chat_id": "b", "texto": "hola"}).json()
    assert otro["respuesta"] == "ok"


def test_limite_total_tambien_aplica_al_webhook(catalogo_prueba):
    cliente = ClienteFalso(respuesta("end_turn", texto("ok")))
    enviados = []
    app = servidor.crear_app(Agente(cliente, Tienda(catalogo_prueba)),
                             lambda n, t: enviados.append(t),
                             limitador=servidor.Limitador(10, 1))
    http = TestClient(app)
    for i in range(2):
        http.post("/webhook", content=json.dumps(aviso_de_texto(f"w{i}", "573", "h")))
    assert enviados == ["ok", servidor.MENSAJE_LIMITE]


def test_limites_desde_el_entorno(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-falsa-de-prueba")
    monkeypatch.setenv("PANEL_CLAVE", "abc")
    monkeypatch.setenv("MAX_MENSAJES_POR_CHAT", "0")
    http = TestClient(servidor.crear_app())
    r = http.post("/api/chat", json={"chat_id": "a", "texto": "hola"})
    assert r.json()["respuesta"] == servidor.MENSAJE_LIMITE
    panel = http.get("/api/reservas", headers={"X-Clave-Panel": "abc"})
    assert panel.status_code == 200


def test_con_supabase_configurado_usa_el_repositorio(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "clave-falsa-de-prueba")
    monkeypatch.setenv("SUPABASE_URL", "https://demo.supabase.co")
    monkeypatch.setenv("SUPABASE_KEY", "sb_secret_prueba")
    monkeypatch.setenv("PANEL_CLAVE", "abc")

    class Vacio:
        def json(self):
            return []

        def raise_for_status(self):
            return None

    pedidas = []
    monkeypatch.setattr(servidor.httpx, "get",
                        lambda url, **o: pedidas.append(url) or Vacio())
    http = TestClient(servidor.crear_app())
    assert pedidas == ["https://demo.supabase.co/rest/v1/reserva"]
    panel = http.get("/api/reservas", headers={"X-Clave-Panel": "abc"})
    assert panel.json()["reservas"] == []
