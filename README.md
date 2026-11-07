# SeminarioIA_Alexyulian21

Agente de WhatsApp y catálogo web para Urban, el almacén de ropa de Alex y su papá (Neiva).
Seminario de IA aplicada al ciclo de vida del software, FET.

## Funcionalidad de la semana 5

### Historia de usuario (documento de requisitos de la semana 3)

**HU-01 (Must).** Como cliente, quiero preguntar si una prenda está disponible en mi talla y cuánto vale
para decidir mi compra sin esperar a que el dueño me responda. Necesidad de origen: N-01.

**Criterios de aceptación**

- **CA-01.1 (prenda disponible):** Dado que en la lista del catálogo la «Polo azul» talla M tiene 3 unidades a $80.000,
  cuando el cliente escribe «¿tiene la polo azul en M?», entonces el asistente responde que sí hay en talla M
  y que el precio es $80.000.
- **CA-01.2 (error, prenda que no está en el catálogo):** Dado que la lista del catálogo no tiene ninguna «chaqueta de cuero»,
  cuando el cliente pregunta por una chaqueta de cuero, entonces el asistente responde que el almacén no la tiene
  en el catálogo y no menciona ningún precio para ella.

Esta funcionalidad es la herramienta `buscar_prenda` del diseño de la semana 4: el precio y las unidades
salen siempre de la lista del catálogo y de las reservas activas, nunca del modelo (RNF-03: nunca ofrecer una prenda agotada).

### Contrato

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

**Ejemplos** (códigos y tallas reales del catálogo; los precios y unidades son de ejemplo hasta cargar los productos)

| Fila del catálogo | Reservas activas de esa prenda | Llamada | Resultado |
|---|---|---|---|
| th-01, Tenis urbano blanco y dorado, 41, $150.000, SI, cantidad 3 | ninguna | `("th-01", "41")` | `{"nombre": "Tenis urbano blanco y dorado", "precio": 150000, "unidades_libres": 3, "hay": True}` (CA-01.1) |
| je-01, Jean azul clásico, 32, $90.000, SI, cantidad 2 | una de 1 unidad | `("je-01", "32")` | `{"nombre": "Jean azul clásico", "precio": 90000, "unidades_libres": 1, "hay": True}` |
| je-01, Jean azul clásico, 32, $90.000, SI, cantidad 2 | dos de 1 unidad | `("je-01", "32")` | `{..., "unidades_libres": 0, "hay": False}` |
| bu-01, Buso negro cuello redondo, M, $85.000, NO, cantidad 4 | ninguna | `("bu-01", "M")` | `{..., "unidades_libres": 0, "hay": False}` |
| go-01, Gorra negra, UNICA, precio 0, SI, cantidad 5 | ninguna | `("go-01", "UNICA")` | `{"nombre": "Gorra negra", "precio": None, "unidades_libres": 5, "hay": True}` |
| (no hay chaqueta de cuero) | — | `("ch-01", "L")` | `PrendaNoEncontrada` (CA-01.2) |
| th-01, Tenis urbano blanco y dorado, 41, ... | — | `("th-01", "45")` | `PrendaNoEncontrada` (talla que no existe) |

### Cómo ejecutar las pruebas

Requisitos: Python 3.11 o más y pytest.

```bash
pip install pytest
pytest
```