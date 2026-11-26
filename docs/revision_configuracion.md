# Revisión del pipeline y del Dockerfile

Proyecto: Agente de WhatsApp y catálogo web para Urban (SeminarioIA_Alexyulian21)
Estudiante: Alex Yulian Caviedes Córdoba
Fecha: [AAAA-MM-DD]

> Instrucciones: copia este archivo en la carpeta docs de tu repositorio. Registra cada problema que encontraste en los archivos generados por IA, antes de corregirlos. Borra las filas de ejemplo antes de entregar.

## 1. Cómo se generaron

**Herramienta de IA:** Claude (Claude Code en la nube), sin contexto del repositorio
**Prompt del pipeline:** «Escribe un workflow de GitHub Actions para mi proyecto de Python con pytest».
**Prompt del Dockerfile:** «Escribe un Dockerfile para mi proyecto de Python que corra las pruebas con pytest».

## 2. Hallazgos

| Archivo y línea | Problema | Riesgo | Corrección |
|---|---|---|---|
| ci.yml (sin línea) | No define `permissions:` | El token usa los permisos por defecto de GitHub, que pueden incluir escritura en el repo | Agregar `permissions: contents: read` |
| ci.yml:14 | Prueba Python 3.9 y 3.10 | El código usa `int \| None` (app/reservas.py), que falla en 3.9; además no coincide con `requires-python` de pyproject.toml | Probar solo las versiones que pide pyproject.toml |
| ci.yml:25 | `pip install pytest` sin versión | Instala la última versión y el resultado cambia de un día a otro | Instalar desde requirements-dev.txt con versiones fijadas |
| ci.yml:26 | Busca `requirements.txt`, que no existe | El `if` lo salta en silencio y nunca instala pytest-cov ni ruff | `pip install -r requirements-dev.txt` |
| ci.yml:28 | Solo corre `pytest` | No corre el linter ni mide cobertura, así que un error de estilo o una caída de cobertura pasa sin avisar | Agregar `ruff check .` y `pytest --cov=app --cov-branch` |
| Dockerfile:1 | `FROM python:3.11` completa | Imagen pesada con muchos paquetes que pueden tener vulnerabilidades | `FROM python:3.11-slim` |
| Dockerfile:3-4 | Copia e instala `requirements.txt`, que no existe | El build falla; y pytest no queda instalado aunque el CMD lo usa | Copiar e instalar `requirements-dev.txt` con `pip install --no-cache-dir` |
| Dockerfile:5 | `COPY . .` sin `.dockerignore` | Copia `.env` con las claves reales, `.git` y `.venv` dentro de la imagen | Crear `.dockerignore` con `.env`, `.git`, `.venv` y las cachés |
| Dockerfile (sin línea) | No hay `USER` | El contenedor corre como root | Crear un usuario sin privilegios y poner `USER app` |
| Dockerfile:6 | `CMD ["pytest"]` | No es un problema: no hay `--reload` ni modo debug, solo corre las pruebas | Ninguna |

## 3. Lo que encontraron las herramientas

| Herramienta | Avisos | ¿Coinciden con mis hallazgos? | ¿Qué no encontró? |
|---|---|---|---|
| actionlint | 0 avisos | No: no encontró ninguno de mis 5 hallazgos del pipeline | Permisos, Python 3.9/3.10, pytest sin versión, requirements.txt inexistente, falta ruff y cobertura |
| hadolint | 1 aviso: DL3042 en la línea 4 (pip sin `--no-cache-dir`) | En parte: coincide con mi fila de Dockerfile:3-4 | Imagen no slim, `.env` copiado sin `.dockerignore`, falta `USER`, requirements.txt inexistente |

## 4. Verificación

- [ ] El pipeline corregido se ejecutó en GitHub y salió en verde: [enlace a la ejecución]
- [ ] Hice fallar una prueba a propósito y el pipeline salió en rojo.
- [ ] La imagen se construye (en mi equipo o en el pipeline).
- [ ] No hay claves en ci.yml, en el Dockerfile ni en el historial de Git.
