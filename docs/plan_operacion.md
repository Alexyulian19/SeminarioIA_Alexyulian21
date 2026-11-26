# Plan de operación y mantenimiento

Proyecto: Agente de WhatsApp y catálogo web para Urban (SeminarioIA_Alexyulian21)
Estudiante: Alex Yulian Caviedes Córdoba
Fecha: 2026-11-26

> Borrador generado con IA a partir de los requisitos no funcionales (RNF-01 a RNF-04, semana 3),
> de los ADR del diseño (semana 4) y del pipeline de la semana 9. Lo revisa Alex.

## 1. Qué está en operación hoy y qué no

| Parte | Estado | Dónde |
|---|---|---|
| Lógica del negocio (`buscar_prenda`, reglas de reservas y `crear_reserva`) | Hecha y probada en local | `app/` y `tests/` |
| Integración continua: linter, pruebas, cobertura de al menos 90 % e imagen de Docker | En operación en cada push y Pull Request a `main` | `.github/workflows/ci.yml`, `Dockerfile` |
| Servicio del agente (webhook de WhatsApp, API de Claude, Google Sheets y Supabase) | No construido: el seminario no pidió despliegue | Diseño, ADR-001 a ADR-003 |

Las secciones 2 a 5 son el plan para cuando el servicio del agente esté en marcha. La sección 6 ya se aplica hoy.

## 2. Qué se monitorea y con qué umbral

Cada umbral sale de un requisito no funcional. Un umbral sin requisito sería una opinión.

| Indicador | Cómo se mide | Requisito | Umbral de alerta | Quién reacciona |
|---|---|---|---|---|
| Tiempo de la primera respuesta | Hora del mensaje recibido y de la respuesta enviada, en el registro del servicio | RNF-01: 60 s en el 95 % de los mensajes | Percentil 95 del día por encima de 60 s | Alex revisa el registro y la API de Claude |
| Disponibilidad del servicio | Un chequeo de salud cada 5 minutos a la ruta del webhook | RNF-02: 99 % al mes (máximo 7,2 h sin servicio) | 3 chequeos seguidos fallidos (15 min caído) o más de 3,6 h caído en el mes (la mitad del margen) | Alex |
| Respuestas correctas del agente | Muestra semanal de 50 preguntas contra la hoja vigente | RNF-03: al menos 45 de 50 y ninguna que ofrezca algo con 0 unidades | Menos de 45 correctas, o **una sola** respuesta que ofrezca una prenda agotada o que no está | Alex y el dueño; se revisa el prompt y las herramientas |
| Reservas dobles | Consulta diaria: unidades reservadas por prenda contra `disponible` en la hoja | ADR-003 y N-04 | Cualquier prenda con más unidades reservadas que disponibles | Alex |
| Avisos de vencimiento | Reservas en efectivo vencidas sin aviso enviado | HU-11 y ADR-003 (aviso hasta 5 min tarde) | Una reserva vencida hace más de 15 minutos sin aviso | Alex |
| Errores de servicios externos | Respuestas de error de WhatsApp, Claude, Google Sheets o Supabase | ADR-001 (si la hoja o Claude fallan, el agente no inventa y pasa al equipo) | Más de 5 errores en 10 minutos de un mismo servicio | Alex |
| Costo | Consumo de la API de Claude y de las plantillas de WhatsApp | ADR-001 (revisar si el costo supera lo que acepte el cliente) | 80 % del límite de gasto del mes configurado en la consola | Alex y el dueño |

> Pendiente: el dueño todavía no ha dicho cuánto puede pagar al mes (pregunta abierta del diseño). Hasta tenerlo, el límite de gasto se pone bajo en la consola del proveedor.

## 3. Qué se registra (y qué no)

- **Se registra:** la hora de cada mensaje y de su respuesta, la herramienta que pidió el modelo (`buscar_prenda`, `crear_reserva`…), el código de la prenda y la talla, el resultado (encontrada, reservada, rechazada y el motivo), los errores de los servicios externos y el número de la reserva.
- **No se registra:** el nombre, el teléfono, la dirección ni el texto completo del mensaje del cliente. El cliente se identifica con un identificador interno de la conversación. Los datos personales solo viven en Supabase, con acceso para los 2 dueños (RNF-04, Ley 1581 de 2012).
- **Cuánto tiempo se guarda:** los registros técnicos, 30 días; los registros de reservas, mientras haga falta para la venta.
- Las claves nunca se registran ni se escriben en el código. Van en variables de entorno (`.env.example`).

## 4. Qué se hace cuando algo falla

| Situación | Qué hace el sistema | Qué hace el equipo |
|---|---|---|
| Google Sheets o la API de Claude no responden | El agente no inventa: responde que un asesor le contesta pronto y pasa la conversación al equipo (`pasar_al_equipo`) | Responde a mano en el mismo chat |
| El servicio se cae | WhatsApp guarda los mensajes; se responden al volver | Alex reinicia el servicio o vuelve a la versión anterior de la imagen |
| Una respuesta ofrece algo agotado | — | Se anota como defecto (`docs/defectos/`), se escribe la prueba que lo reproduce y se corrige antes de volver a subir |
| Se reserva dos veces la misma unidad | — | El equipo llama al segundo cliente y se revisa el bloqueo de ADR-003 |

**Volver atrás:** cada versión sale de `main` con el pipeline en verde y una imagen de Docker. Si una versión nueva falla, se vuelve a la imagen anterior y se abre un defecto.

## 5. Mantenimiento

| Tarea | Frecuencia | Herramienta |
|---|---|---|
| Revisar vulnerabilidades de las dependencias | Cada mes y antes de cada versión | `pip-audit` (semana 6) |
| Actualizar las versiones fijadas en `requirements-dev.txt` | Cada mes, en una rama, con el pipeline en verde | GitHub Actions |
| Volver a correr la muestra de 50 preguntas | Cada semana, y siempre que cambie el prompt, el modelo o el formato de la hoja | Lista de preguntas de prueba (PR-13) |
| Revisar la versión del modelo de lenguaje | Cuando el proveedor anuncie una nueva o retire la actual | Consola del proveedor |
| Revisar que el equipo baje `disponible` en la hoja al entregar | Cada semana | Consulta de reservas dobles (sección 2) |
| Revisar los costos del mes | Cada mes | Consola del proveedor |

Todo cambio entra por una rama y un Pull Request, con el pipeline en verde y revisión del diff antes de unirlo a `main`.

## 6. Lo que ya se aplica hoy

- El pipeline corre `ruff`, las 72 pruebas, la cobertura (mínimo 90 %; hoy 100 % de ramas en `app/`) y construye y prueba la imagen de Docker en cada Pull Request.
- Una prueba rota pone el pipeline en rojo (comprobado en la semana 9).
- Los datos de prueba son sintéticos y no hay claves en el repositorio ni en la imagen (`.gitignore` y `.dockerignore`).
