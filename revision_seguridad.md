# Informe de revisión de código y seguridad

**Proyecto:** Agente de WhatsApp y catálogo web para Urban

**Estudiante:** Alex Yulian Caviedes Córdoba

**Fecha:** 2026-11-14

**Commit revisado:** `ca229ee`

## 1. Herramientas y criterios

| Herramienta | Versión | Uso |
| --- | --- | --- |
| ruff | 0.17.5 | Linter con reglas E, F, B, S, I; configuración en `pyproject.toml`. |
| pip-audit | 2.10.1 | Auditoría de `requirements-dev.txt` (`pytest==9.2.0`, `ruff==0.17.5`). |
| pytest | 9.2.0 | Pruebas de HU-01. |
| Claude Code (Opus 5.5) | — | Revisión asistida por IA (sección 3). |

**Criterios:** OWASP Top 10 2021 y el contrato de `buscar_prenda` del README.

| Punto de seguridad | ¿Aplica? | Resultado |
| --- | --- | --- |
| Inyección | No | No hay SQL, shell ni `eval`; la función solo compara datos que ya están en memoria. |
| Secretos | Sí | Sin claves en el código ni en el historial (`git log -- .env` vacío, `git grep` sin claves). `.gitignore` excluye `.env` y `.env.*`; `!.env.example` solo tiene valores de relleno. |
| Contraseñas | No | La función no autentica a nadie. |
| Control de acceso | No (en esta función) | Lee el catálogo público y no maneja datos personales. Se hará en el webhook. |
| Dependencias | Sí | La app solo usa la librería estándar. pip-audit no encontró vulnerabilidades en las dependencias de desarrollo. |

## 2. Tabla de hallazgos

| Id | Archivo y línea | Problema | Categoría (OWASP o tipo) | Severidad | Corrección | Commit |
| --- | --- | --- | --- | --- | --- | --- |
| H-01 | `tests/test_buscar_prenda.py:1`, `:10` | Líneas largas (E501) y faltaba configuración del linter | Estilo | baja | Configurar ruff (E, F, B, S, I) en `pyproject.toml` y partir las líneas largas | `b1a679d` |
| H-02 | raíz | Faltaban `.env.example` y dependencias fijadas | A05 / A06 | media | Agregar `.env.example` con valores de relleno y `requirements-dev.txt` con versiones fijadas | `0129c83` |
| H-03 | `tests/test_buscar_prenda.py` | Falta prueba del límite «cantidad 0» del README | Cobertura | media | Prueba `test_cantidad_cero_no_hay` | `3899f6d` |
| H-04 | `tests/test_buscar_prenda.py` | No se probaba que `PrendaNoEncontrada` herede de `LookupError` | Cobertura | baja | Prueba `test_prenda_no_encontrada_es_lookup_error` | `3899f6d` |
| H-05 | `app/buscar_prenda.py` | `fila["precio"] or None` dejaba la regla implícita | Legibilidad / valor mágico | baja | Constante `PRECIO_CONSULTAR` y comparación explícita | `ff05753` |
| H-06 | `app/buscar_prenda.py` | Condición código + talla duplicada | Duplicación | baja | Función privada `_es_misma_prenda`, usada en los dos lugares | `4eb3a40` |
| H-07 | `pyproject.toml` | No declaraba Python 3.11 | Configuración | baja | `[project]` con `requires-python = ">=3.11"` y `version = "0.1.0"`; `target-version = "py311"` en ruff | `54e6a07`, `09ca9b5` |
| H-08 | `app/buscar_prenda.py` | Docstrings sin Args, Returns ni Raises | Documentación | baja | Docstrings en español con Args, Returns y Raises, según el README | `99db1bb` |

Las correcciones las hizo un agente en la rama `agente/revision-semana6`. Revisé el diff con `git diff main..agente/revision-semana6` y lo integré con merge (fast-forward).

### Avisos del linter no corregidos

Antes: 15 avisos (13 S101 y 2 E501, todos en `tests/`). Después: 0.

| Regla | Archivo y línea | Por qué se mantiene |
| --- | --- | --- |
| S101 | `tests/*` | `assert` es la forma normal de comprobar en pytest. |

## 3. Revisión con IA

Herramienta: Claude Code (Opus 5.5) en VS Code, en modo Manual y solo lectura, con el prompt de revisión de la semana (Rol, Contexto, Tarea, Formato, Restricciones).

| Hallazgo de la IA | ¿Real o falso positivo? | Cómo lo verifiqué |
| --- | --- | --- |
| Falta prueba de cantidad 0 | Real | Leí `README.md:70` y no había prueba para ese límite; corrí pytest tras agregarla (12 pasan). |
| No se prueba la herencia de `LookupError` | Real | Leí `README.md:54` y ninguna prueba lo comprobaba; corrí pytest tras agregarla. |
| `fila["precio"] or None` deja la regla implícita | Real | Leí `app/buscar_prenda.py:53`; tras cambiarlo por `PRECIO_CONSULTAR`, pytest siguió en verde sin tocar las pruebas. |
| Falta `requires-python` | Real | Leí `pyproject.toml` y no declaraba la versión de Python; corrí ruff y pytest tras agregarla. |
| Trazabilidad del CA-01.1 (README usa «Polo azul», la prueba usa `th-01`) | Real, menor | Comparé `README.md:15` con `tests/test_buscar_prenda.py:41`. Queda pendiente. |

- **Falsos positivos:** ninguno. Las sospechas que dependen de los datos reales (sección 4) no se clasifican como reales hasta tener el lector de la hoja.
- **Lo que la IA no encontró:** la condición código + talla duplicada (H-06). La encontré yo con la lista de revisión.

## 4. Pendientes

| Pendiente | Por qué no se corrigió todavía | Plan |
| --- | --- | --- |
| Google Sheets puede entregar los datos como texto (`"0"`, `"3"`, `"Si "`) | El lector de la hoja aún no existe; la función recibe los datos ya leídos. | Normalizar los tipos en el lector de la hoja. |
| Reservas con cantidad negativa aumentarían las unidades libres | La base de datos en Supabase aún no está creada. | `CHECK (cantidad >= 1)` en la tabla de reservas. |
| Filas duplicadas en la hoja | El lector de la hoja aún no existe. | Validar al cargar la hoja. |
| Log injection por el mensaje de `PrendaNoEncontrada` (incluye código y talla) | Todavía no hay logging. | Sanear el texto cuando se agregue logging. |
| Trazabilidad del CA-01.1 en el README | El agente solo podía tocar `app/`, `tests/` y `pyproject.toml`. | Usar un producto real del catálogo en el CA-01.1 o explicar la relación con `th-01`. |
| Las pruebas se corrieron en Python 3.13, no en 3.11 | El entorno virtual usa Python 3.13. | Correr las pruebas en Python 3.11. |

### Claves expuestas

Ninguna.
