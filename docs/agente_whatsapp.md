# Agente de WhatsApp (semana 10)

El agente conversa con el cliente usando Claude (API de Anthropic) y cuatro
herramientas. Claude solo decide **qué** herramienta usar y **cómo** redactar;
precios, unidades, totales y vencimientos salen siempre de las funciones
probadas de `app/` (RNF-03).

```text
Cliente ──► chat local (navegador) ──┐
       └──► WhatsApp ─► Meta ─► /webhook ──► Agente (Claude) ──► Tienda
                                                         buscar_productos   (catalogo.py)
                                                         consultar_prenda   (buscar_prenda)
                                                         crear_reserva      (reservar + reservas)
                                                         pasar_a_dueno      (aviso al panel)
```

| Archivo | Qué hace |
| --- | --- |
| `app/catalogo.py` | Lee `datos/catalogo.csv` (el CSV de la web) y busca por palabras |
| `app/herramientas.py` | Las 4 herramientas y la `Tienda` (reservas en memoria, con color) |
| `app/agente.py` | El ciclo con Claude: pregunta → herramienta → resultado → respuesta |
| `app/servidor.py` | FastAPI: página de chat, `/api/chat`, `/api/reservas` y `/webhook` de Meta |
| `app/web/chat.html` | Chat tipo WhatsApp + panel del dueño (para la demo y el video) |
| `app/consola.py` | El mismo chat en la terminal |

Las pruebas (`tests/test_agente.py`, `test_herramientas.py`, `test_servidor.py`,
`test_catalogo.py`) usan un **cliente de Claude falso** (`tests/falsos.py`): no
llaman a la API, no gastan dinero y no necesitan clave.

## A. Correrlo en local

1. Crea tu clave en https://console.anthropic.com → *API Keys* → *Create Key*.
   Pon un límite de gasto en *Billing → Limits*. La clave va **solo** en `.env`.
2. En la raíz del proyecto:

```powershell
pip install -r requirements-dev.txt
copy .env.example .env      # si ya tienes .env, no lo copies: agrega la línea
notepad .env                # pega tu clave en ANTHROPIC_API_KEY=...
uvicorn app.servidor:crear_app --factory --reload
```

3. Abre http://127.0.0.1:8000 y escribe como cliente. A la derecha, el panel
   del dueño muestra las reservas y los avisos.

Para la terminal en vez del navegador: `python -m app.consola`.

## B. (Opcional) Conectarlo a WhatsApp real con el número de prueba de Meta

No es necesario para la entrega (el profesor pide el sistema funcional en local).

1. En https://developers.facebook.com crea una app tipo *Business* y agrega el
   producto **WhatsApp**. En *API Setup* copia el *token temporal* y el
   *Phone number ID*, y agrega tu celular como número de prueba.
2. En *App settings → Basic* copia el *App Secret*.
3. Llena en `.env`: `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`,
   `WHATSAPP_APP_SECRET` y un `WHATSAPP_VERIFY_TOKEN` inventado por ti.
4. Expón tu servidor con ngrok (`ngrok http 8000`) y en *WhatsApp → Configuration*
   pon *Callback URL* = `https://<tu-ngrok>/webhook` y el mismo *Verify token*.
   Suscríbete al campo `messages`.
5. Escríbele al número de prueba desde tu celular.

El servidor revisa la firma `X-Hub-Signature-256` de cada aviso y no responde
dos veces el mismo mensaje si Meta lo reenvía.

## Supuestos y límites (para revisar)

- **Cantidad vacía = 5.** La columna `cantidad` del catálogo hoy está vacía
  (no se lleva inventario). El agente la toma como 5 (el máximo de una
  reserva). Si se llena la hoja con cantidades reales, se usan esas.
- **Reservas en memoria.** Se pierden al reiniciar el servidor. Guardarlas en
  Supabase queda como trabajo futuro.
- **Color.** Si un producto tiene varios colores y el cliente no dice cuál, la
  herramienta responde con la lista de colores para que el agente pregunte.
- **Modelo.** Por defecto `claude-opus-5-5` con esfuerzo bajo (respuestas
  rápidas de chat). Se cambia con `ANTHROPIC_MODEL` en el `.env`.
- **Datos personales (Ley 1581).** Los mensajes del cliente se envían a la API
  de Anthropic. En las pruebas y la demo solo se usan nombres inventados.
