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
| Ejemplo: ci.yml:9 | permissions: write-all | El pipeline puede modificar todo el repositorio | permissions: contents: read |
| Ejemplo: Dockerfile:1 | FROM python:latest | Cambia sin aviso; imagen pesada | FROM python:3.12-slim |
| | | | |

## 3. Lo que encontraron las herramientas

| Herramienta | Avisos | ¿Coinciden con mis hallazgos? | ¿Qué no encontró? |
|---|---|---|---|
| actionlint | | | |
| hadolint | | | |

## 4. Verificación

- [ ] El pipeline corregido se ejecutó en GitHub y salió en verde: [enlace a la ejecución]
- [ ] Hice fallar una prueba a propósito y el pipeline salió en rojo.
- [ ] La imagen se construye (en mi equipo o en el pipeline).
- [ ] No hay claves en ci.yml, en el Dockerfile ni en el historial de Git.
