# SeminarioIA_Alexyulian21

## 1. Qué es

Un agente de WhatsApp y un catálogo web para que los clientes de Urban, el almacén de ropa de mi familia en Neiva,
consulten prendas, tallas y precios sin esperar a que el dueño les responda.

## 2. Requisitos

- Python 3.11 o superior.
- Dependencias de desarrollo en `requirements-dev.txt` (pytest y ruff, con versiones fijadas).
- La app solo usa la librería estándar de Python.

## 3. Instalación

En Windows PowerShell:

```powershell
git clone https://github.com/Alexyulian19/SeminarioIA_Alexyulian21.git
cd SeminarioIA_Alexyulian21
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
copy .env.example .env
```

Si PowerShell no deja ejecutar `Activate.ps1`, ejecuta una vez
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a intentarlo.
El archivo `.env` es solo local (está en `.gitignore`); llena allí tus claves reales, nunca en `.env.example`.

## 4. Ejecución

El webhook de WhatsApp todavía no existe. Hoy la funcionalidad disponible es la función `buscar_prenda`,
que se puede probar desde la raíz del proyecto con un catálogo de una fila:

```powershell
python -c "from app.buscar_prenda import buscar_prenda; catalogo = [{'codigo': 'th-01', 'nombre': 'Tenis urbano blanco y dorado', 'talla': '41', 'precio': 150000, 'disponible': 'SI', 'cantidad': 3}]; print(buscar_prenda(catalogo, [], 'th-01', '41'))"
```

Salida:

```text
{'nombre': 'Tenis urbano blanco y dorado', 'precio': 150000, 'unidades_libres': 3, 'hay': True}
```

### Funcionalidad de la semana 5: HU-01

#### Historia de usuario (documento de requisitos de la semana 3)

**HU-01 (Must).** Como cliente, quiero preguntar si una prenda está disponible en mi talla y cuánto vale
para decidir mi compra sin esperar a que el dueño me responda. Necesidad de origen: N-01.

#### Criterios de aceptación

- **CA-01.1 (prenda disponible):** Dado que en la lista del catálogo el «Tenis urbano blanco y dorado» (`th-01`) talla 41
  tiene 3 unidades a $150.000, cuando el cliente escribe «¿tiene el tenis urbano blanco y dorado en 41?», entonces el asistente
  responde que sí hay en talla 41 y que el precio es $150.000.
- **CA-01.2 (error, prenda que no está en el catálogo):** Dado que la lista del catálogo no tiene ninguna «chaqueta de cuero»,
  cuando el cliente pregunta por una chaqueta de cuero, entonces el asistente responde que el almacén no la tiene
  en el catálogo y no menciona ningún precio para ella.

Esta funcionalidad es la herramienta `buscar_prenda` del diseño de la semana 4: el precio y las unidades
salen siempre de la lista del catálogo y de las reservas activas, nunca del modelo (RNF-03: nunca ofrecer una prenda agotada).

#### Contrato

```python
def buscar_prenda(
    catalogo: list[dict],
    reservas_activas: list[dict],
    codigo: str,
    talla: str,
) -> dict:
```

**Recibe**

- `catalogo`: filas de la lista del catálogo (Google Sheets), ya leídas, una fila por producto y talla. Cada fila tiene, al menos,
  `codigo` (el `id` del catálogo web, por ejemplo `"th-01"`), `nombre`, `talla`, `precio` (entero en pesos;
  0 significa «Consultar precio», igual que en la web), `disponible` («SI» o «NO») y `cantidad` (entero, 0 o más).
- `reservas_activas`: reservas sin vencer. Cada una tiene `codigo`, `talla` y `cantidad` (entero, 1 o más).
- `codigo` y `talla`: la prenda por la que pregunta el cliente, por ejemplo `"th-01"` y `"41"`.

**Devuelve** un diccionario con:

- `nombre`: el nombre de la prenda en el catálogo.
- `precio`: el precio de la fila, en pesos, o `None` si la fila tiene precio 0 («Consultar precio»).
- `unidades_libres`: `cantidad` de la fila − suma de las `cantidad` de las reservas activas de esa misma
  prenda y talla. Nunca es negativo.
- `hay`: `True` si `unidades_libres` es mayor que 0; si no, `False`.

**Errores**

- Lanza `PrendaNoEncontrada` (subclase de `LookupError`) si no hay ninguna fila con ese `codigo` y esa `talla`.
  En ese caso no se devuelve ningún precio (CA-01.2).

**Supuestos**

- Hay una sola fila por combinación de código y talla. El color no es un parámetro porque en el catálogo
  cada código ya es un color (por ejemplo, `je-01` es el «Jean azul clásico» y `je-02` el «Jean negro»).
- La comparación es exacta. Convertir «¿tienen el jean azul en 32?» en `("je-01", "32")` lo hace el agente antes de llamar a la función.
- La talla es texto: «38» a «43» en tenis de hombre, «35» a «39» en tenis de dama, «S» a «XL» en ropa,
  «28» a «36» en jeans y bermudas, y «UNICA» en las gorras (talla única).
- La función no modifica las listas que recibe ni lee la hoja o la base de datos: recibe los datos ya leídos.

**Casos límite**

- Si las reservadas son iguales a la cantidad, devuelve `unidades_libres = 0` y `hay = False`.
- Si `disponible` es «NO», devuelve `unidades_libres = 0` y `hay = False`, aunque `cantidad` sea mayor que 0.
- Si `cantidad` es 0, devuelve `hay = False`.
- Si hay más reservadas que cantidad (dato inconsistente), devuelve `unidades_libres = 0` y nunca un número negativo.
- Si no hay reservas activas, devuelve la `cantidad` de la fila.
- Si el catálogo está vacío, lanza `PrendaNoEncontrada`.
- Si `precio` es 0, devuelve `precio = None` para que el asistente diga «Consultar precio» y nunca invente un valor.
- Si `precio` está vacío (`""`), devuelve `precio = None`.

**Ejemplos** (códigos y tallas reales del catálogo; los precios y unidades son de ejemplo hasta cargar los productos)

| Fila del catálogo | Reservas activas de esa prenda | Llamada | Resultado |
| --- | --- | --- | --- |
| th-01, Tenis urbano blanco y dorado, 41, $150.000, SI, cantidad 3 | ninguna | `("th-01", "41")` | `{"nombre": "Tenis urbano blanco y dorado", "precio": 150000, "unidades_libres": 3, "hay": True}` (CA-01.1) |
| je-01, Jean azul clásico, 32, $90.000, SI, cantidad 2 | una de 1 unidad | `("je-01", "32")` | `{"nombre": "Jean azul clásico", "precio": 90000, "unidades_libres": 1, "hay": True}` |
| je-01, Jean azul clásico, 32, $90.000, SI, cantidad 2 | dos de 1 unidad | `("je-01", "32")` | `{..., "unidades_libres": 0, "hay": False}` |
| bu-01, Buso negro cuello redondo, M, $85.000, NO, cantidad 4 | ninguna | `("bu-01", "M")` | `{..., "unidades_libres": 0, "hay": False}` |
| go-01, Gorra negra, UNICA, precio 0, SI, cantidad 5 | ninguna | `("go-01", "UNICA")` | `{"nombre": "Gorra negra", "precio": None, "unidades_libres": 5, "hay": True}` |
| (no hay chaqueta de cuero) | — | `("ch-01", "L")` | `PrendaNoEncontrada` (CA-01.2) |
| th-01, Tenis urbano blanco y dorado, 41, ... | — | `("th-01", "45")` | `PrendaNoEncontrada` (talla que no existe) |

## 5. Pruebas

Con el entorno virtual activado, desde la raíz del proyecto:

```powershell
pytest
ruff check --select E,F,B,S .
```

Hay 57 pruebas:

- 13 de HU-01 en `tests/test_buscar_prenda.py`: casos normales, casos límite del contrato y casos de error.
- 44 de las reglas de reservas (semana 7) en `tests/test_reservas.py`: vencimiento de 24 h, forma de pago,
  total y si se puede reservar. Cada fila de `parametrize` lleva el id de su caso (por ejemplo `R1-5` o `D2`),
  y algunas pruebas usan los datos sintéticos de `tests/datos/` a través del fixture de `tests/conftest.py`.

Las reglas, las tablas de casos, la revisión de las pruebas de la IA y los cambios para romper el código
están en [registro_pruebas.md](registro_pruebas.md).

## 6. Estructura

| Ruta | Contenido |
| --- | --- |
| `app/` | Código de la aplicación: `buscar_prenda.py` (HU-01) y `reservas.py` (reglas de las reservas). |
| `tests/` | Pruebas con pytest y `conftest.py` con el fixture de datos sintéticos. |
| `tests/datos/` | Datos sintéticos de reservas (CSV, ninguna persona real). |
| `registro_pruebas.md` | Registro de pruebas de la semana 7. |
| `pyproject.toml` | Versión de Python y configuración de pytest y ruff. |
| `requirements-dev.txt` | Dependencias de desarrollo con versiones fijadas. |
| `.env.example` | Plantilla de variables de entorno, con valores de relleno. |
| `revision_seguridad.md` | Informe de revisión de código y seguridad (semana 6). |
| `bitacora_ia.md` | Bitácora de uso de IA. |

## 7. Uso de IA

- Claude en chat ayudó a redactar el contrato y las pruebas de HU-01, y Claude Code en VS Code (modo Manual) implementó y refactorizó `buscar_prenda`.
- Cada sugerencia se verificó con pytest y contra el catálogo real, y se aceptó, se ajustó o se rechazó (por ejemplo, se quitó un parámetro `color` que el catálogo no tiene).
- En la semana 6, Claude Code revisó el código en modo solo lectura y un agente aplicó las correcciones en una rama aparte, que revisé antes del merge.
- En la semana 7, la IA propuso los casos, las pruebas y los datos sintéticos a partir de mis reglas. Cada prueba se revisó con las tres preguntas (esperado de la regla, fallaría si rompo el código, no redundante) y el código se rompió a propósito 5 veces (rama `semana7-pruebas`).

Detalle en [bitacora_ia.md](bitacora_ia.md), [revision_seguridad.md](revision_seguridad.md) y [registro_pruebas.md](registro_pruebas.md).

## 8. Autor y licencia

Alex Yulian Caviedes Córdoba. FET, Seminario de IA aplicada al ciclo de vida del software, 2026.

Licencia: Uso académico, todos los derechos reservados.
