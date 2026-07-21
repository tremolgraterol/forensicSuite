# ForensicSuite - Notas de Lanzamiento

**Version:** 2.0.0  
**Fecha:** 21 de julio de 2026  
**Plataformas soportadas:** Linux (Live USB) y Windows 10/11

---

## Descargas disponibles

| Asset | Descripcion | Plataforma |
|---|---|---|
| `Source code (zip/tar.gz)` | Codigo fuente completo con documentacion | Linux / Windows |
| `forensic-suite-live.iso` | Imagen ISO Live USB con Debian 13 (trixie) + herramientas forenses | Linux Live |
| `forensic_suite_windows.zip` (opcional) | Ejecutable portable `.exe` generado con PyInstaller | Windows 10/11 |

> **Nota:** La ISO pesa aproximadamente 1,3 GB. Descargala una sola vez y verifica su hash SHA-256.

---

## Inicio rapido

### Opcion 1: USB/ISO Live forense (recomendado para adquisicion forense)

1. Descarga `forensic-suite-live.iso`.
2. Graba la ISO en un USB de al menos 4 GB.
3. Arranca el equipo objetivo desde el USB.
4. Usa ForensicSuite desde el entorno Live sin alterar el disco interno.

**Instrucciones completas:** [`docs/CREAR_USB_LIVE.md`](docs/CREAR_USB_LIVE.md)

### Opcion 2: Windows

1. Descarga el ejecutable `forensic_suite.exe` o el codigo fuente.
2. Si usas el codigo fuente, instala Python 3.9+ y las dependencias:
   ```powershell
   pip install -e ".[full]"
   pip install volatility3
   ```
3. Ejecuta:
   ```powershell
   forensic_suite.exe --help
   # o desde codigo fuente
   python -m forensic_suite_windows.win_main --help
   ```

**Instrucciones completas:** [`docs/INSTALACION_WINDOWS.md`](docs/INSTALACION_WINDOWS.md)

---

## Verificacion de integridad

Todos los assets publicados incluyen hashes SHA-256. Verifica con:

```bash
sha256sum forensic-suite-live.iso
```

Compara el resultado con el hash publicado en el release.

---

## Contenido de la ISO Live

- Debian 13 (trixie) amd64
- ForensicSuite instalado en `/opt/forensic_suite`
- Entorno virtual Python con Volatility3, requests, cryptography, psutil
- Herramientas forenses: dd, dc3dd, scalpel, bulk_extractor (reducido), fls, xxd, hashdeep, entre otras
- `mforense` con LiME y AVML para adquisicion de memoria RAM

---

## Version Windows

- Punto de entrada separado: `forensic_suite_windows/win_main.py`
- Capa de abstraccion Windows: `forensic_suite_windows/core/plataforma.py`
- Funciones disponibles: hash, manifest, acta, firma GPG, timestamp, carve, analyze, memoria --analizar (Volatility3), interact, listar discos, proteccion USB global.
- Limitaciones: bloqueo real por dispositivo y daemon no son equivalentes a Linux; adquisicion RAM requiere WinPmem/DumpIt.

---

## Documentacion incluida

| Documento | Descripcion |
|---|---|
| [`docs/CREAR_USB_LIVE.md`](docs/CREAR_USB_LIVE.md) | Como crear y usar el USB/ISO Live |
| [`docs/INSTALACION_WINDOWS.md`](docs/INSTALACION_WINDOWS.md) | Instalacion, build y uso en Windows |
| [`docs/01_GUIA_USUARIO.md`](docs/01_GUIA_USUARIO.md) | Guia del perito |
| [`docs/02_GUIA_TECNICA.md`](docs/02_GUIA_TECNICA.md) | Detalle tecnico |
| [`docs/03_PROTOCOLO_FORENSE.md`](docs/03_PROTOCOLO_FORENSE.md) | Protocolo paso a paso |
| [`docs/04_VERIFICACION_CONTRA_PERITAJE.md`](docs/04_VERIFICACION_CONTRA_PERITAJE.md) | Verificacion por contra perito |
| [`docs/MANUAL_FORENSIC_SUITE.md`](docs/MANUAL_FORENSIC_SUITE.md) | Manual completo |

---

## Soporte

Para reportar problemas o consultas, usa la seccion **Issues** del repositorio.
