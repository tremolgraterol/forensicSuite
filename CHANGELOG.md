# Changelog

Todos los cambios notables de ForensicSuite se documentarán en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## [2.0.0] - 2026-07-21

### Added

- Lanzamiento público de ForensicSuite v2.0.0.
- CLI multiplataforma: Linux (`forensic_suite/__main__.py`) y Windows (`forensic_suite_windows/win_main.py`).
- Cálculo de hashes SHA-256, SHA-512 y MD5 con generación de archivos consolidados.
- Verificación de hashes automática desde archivos `.hash`.
- Generación de actas de cadena de custodia formato MP 2017 (Markdown + JSON).
- Firma digital con GPG y verificación detached.
- Sellos de tiempo RFC 3161 y verificación de tokens TSA.
- Manifiestos JSON canónicos de directorios de evidencia.
- Carving de archivos eliminados con Scalcel y Foremost.
- Perfiles de carving predefinidos: imágenes, documentos, mensajería.
- Análisis de memoria RAM con Volatility3.
- Daemon de bloqueo automático USB con regla udev y servicio systemd.
- Bloqueo lógico de dispositivos en Linux con detección de disco raíz.
- Modo interactivo para casos forenses.
- Generación de ISO Live forense basada en Debian 13 (trixie).
- Build portable para Windows con PyInstaller.
- Documentación extensa en `docs/`.
- Wiki de GitHub con guías de instalación, comandos y FAQ.
- Discusiones de GitHub para soporte comunitario.
- Archivos `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md` y `LICENSE` (MIT).

### Changed

- Redirección automática del CLI Linux al CLI Windows cuando se ejecuta en `win32`.
- Ajustes en `forensic_suite.spec` y scripts de build para compatibilidad con PyInstaller 6.x (layout `onedir`).

### Fixed

- Eliminación de opciones `--onedir` / `--onefile` en invocaciones de PyInstaller con archivo `.spec`.
- Rutas de salida del ejecutable Windows actualizadas a `dist/windows/forensic_suite/`.
- Instrucciones para ejecutar el `.exe` sin firma pese a SmartScreen/Defender.

## [Unreleased]

### Added

- Plantillas de Issues y Pull Requests.

### Changed

- Mejoras en documentación y sección de comunidad del README.

### Fixed

- N/A.
