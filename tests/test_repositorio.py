"""Pruebas de guardar y leer reservas en Supabase, con un HTTP falso (sin red)."""

from datetime import datetime

import httpx
import pytest

from app.herramientas import HORA_COLOMBIA, Tienda
from app.repositorio import RepositorioSupabase

AHORA = datetime(2026, 11, 27, 10, 0, tzinfo=HORA_COLOMBIA)
URL = "https://demo.supabase.co/"


class RespuestaFalsa:
    def __init__(self, datos=None, codigo=200):
        self.datos = datos
        self.codigo = codigo

    def json(self):
        return self.datos

    def raise_for_status(self):
        if self.codigo >= 400:
            peticion = httpx.Request("POST", URL)
            raise httpx.HTTPStatusError(
                "error", request=peticion,
                response=httpx.Response(self.codigo, request=peticion),
            )


class HttpFalso:
    """Guarda las peticiones y devuelve respuestas fijas."""

    def __init__(self, filas=None, codigo_post=200, falla_get=False):
        self.filas = filas or []
        self.codigo_post = codigo_post
        self.falla_get = falla_get
        self.posts: list[dict] = []
        self.gets: list[dict] = []

    def post(self, url, **opciones):
        self.posts.append({"url": url, **opciones})
        return RespuestaFalsa(codigo=self.codigo_post)

    def get(self, url, **opciones):
        self.gets.append({"url": url, **opciones})
        if self.falla_get:
            raise httpx.ConnectError("sin red")
        return RespuestaFalsa(self.filas)


FILA = {
    "numero": "R-0001", "chat_id": "573001", "nombre_cliente": "Valentina Rojas",
    "forma_pago": "efectivo", "total": 270000,
    "creada_en": "2026-11-27T15:00:00+00:00",
    "vence_en": "2026-11-28T15:00:00+00:00",
    "linea_reserva": [{"codigo": "th-08", "color": "Suela beige", "talla": "41",
                       "nombre_prenda": "Adidas Campus", "cantidad": 2}],
}


def reservar(tienda, **cambios):
    datos = dict(codigo="th-08", talla="41", color="Suela beige", cantidad=2,
                 forma_pago="efectivo", cliente="Valentina Rojas", chat_id="573001")
    datos.update(cambios)
    return tienda.reservar(**datos)


@pytest.mark.parametrize("clave, con_bearer", [
    ("sb_secret_abc", False),
    ("eyJhbGciOi.jwt.antiguo", True),
])
def test_cabeceras_segun_el_tipo_de_clave(clave, con_bearer):
    repo = RepositorioSupabase(URL, clave, HttpFalso())
    assert repo.cabeceras["apikey"] == clave
    assert ("Authorization" in repo.cabeceras) == con_bearer
    assert repo.base == "https://demo.supabase.co/rest/v1"


def test_guardar_manda_reserva_y_linea_en_una_llamada(catalogo_prueba):
    http = HttpFalso()
    tienda = Tienda(catalogo_prueba, lambda: AHORA, RepositorioSupabase(URL, "k", http))
    reservar(tienda)
    assert len(http.posts) == 1
    llamada = http.posts[0]
    assert llamada["url"].endswith("/rest/v1/rpc/guardar_reserva")
    datos = llamada["json"]["datos"]
    assert datos["numero"] == "R-0001"
    assert datos["total"] == 270000
    assert datos["precio_unitario"] == 135000
    assert datos["vence_en"] == "2026-11-28T10:00:00-05:00"
    assert datos["color"] == "Suela beige"


def test_reserva_por_nequi_se_guarda_sin_vencimiento(catalogo_prueba):
    http = HttpFalso()
    tienda = Tienda(catalogo_prueba, lambda: AHORA, RepositorioSupabase(URL, "k", http))
    reservar(tienda, forma_pago="Nequi", cantidad=1)
    assert http.posts[0]["json"]["datos"]["vence_en"] is None


def test_al_arrancar_lee_las_reservas_guardadas(catalogo_prueba):
    http = HttpFalso([FILA, {**FILA, "numero": "R-0002", "vence_en": None,
                             "linea_reserva": []}])
    tienda = Tienda(catalogo_prueba, lambda: AHORA, RepositorioSupabase(URL, "k", http))
    assert [r["numero"] for r in tienda.reservas] == ["R-0001", "R-0002"]
    primera = tienda.reservas[0]
    assert primera["creada_en"] == AHORA
    assert primera["cantidad"] == 2
    assert tienda.reservas[1]["codigo"] == ""
    assert http.gets[0]["params"]["order"] == "id.asc"
    # La reserva leída descuenta unidades y la siguiente sigue la numeración.
    assert tienda.consultar_prenda("th-08", "41", "Suela beige")["hay"] is False
    nueva = reservar(tienda, color="Suela blanca", cantidad=1)
    assert nueva["numero"] == "R-0003"


def test_si_la_base_no_responde_al_arrancar_sigue_en_memoria(catalogo_prueba):
    repo = RepositorioSupabase(URL, "k", HttpFalso(falla_get=True))
    tienda = Tienda(catalogo_prueba, lambda: AHORA, repo)
    assert tienda.reservas == []


def test_si_no_se_puede_guardar_avisa_al_dueno(catalogo_prueba):
    repo = RepositorioSupabase(URL, "k", HttpFalso(codigo_post=500))
    tienda = Tienda(catalogo_prueba, lambda: AHORA, repo)
    reserva = reservar(tienda)
    assert tienda.reservas == [reserva]
    assert "R-0001 no quedó guardada" in tienda.avisos_dueno[0]["motivo"]
