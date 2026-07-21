# ForensicSuite - Notas de Lanzamiento

**Version:** 2.0.0  
**Fecha:** 21 de julio de 2026

ForensicSuite se publica en **dos releases separadas** segun plataforma:

- **Linux / Live USB:** para adquisicion y analisis forense completo.
- **Windows:** para analisis de evidencias y memoria con Volatility3 en entornos Windows.

---

## Release Linux / Live USB

**Tag recomendado:** `v2.0.0-linux-live`  
**Nombre:** `ForensicSuite 2.0.0 — Linux Live USB`

### Descargas

| Asset | Descripcion |
|---|---|
| `forensic-suite-live.iso` | Imagen ISO Live USB con Debian 13 (trixie) + herramientas forenses |
| `forensic-suite-live.iso.sha256` | Hash SHA-256 de la ISO |
| `Source code (zip/tar.gz)` | Codigo fuente completo |

> **Nota:** La ISO pesa aproximadamente 1,3 GB. Descargala una sola vez y verifica su hash SHA-256.

### Inicio rapido

1. Descarga `forensic-suite-live.iso`.
2. Graba la ISO en un USB de al menos 4 GB.
3. Arranca el equipo objetivo desde el USB.
4. Usa ForensicSuite desde el entorno Live sin alterar el disco interno.

**Instrucciones completas:** [`docs/CREAR_USB_LIVE.md`](docs/CREAR_USB_LIVE.md)

### Contenido de la ISO Live

- Debian 13 (trixie) amd64
- ForensicSuite instalado en `/opt/forensic_suite`
- Entorno virtual Python con Volatility3, requests, cryptography, psutil
- Herramientas forenses: dd, dc3dd, scalpel, bulk_extractor (reducido), fls, xxd, hashdeep, entre otras
- `mforense` con LiME y AVML para adquisicion de memoria RAM

---

## Release Windows

**Tag recomendado:** `v2.0.0-windows`  
**Nombre:** `ForensicSuite 2.0.0 — Windows`

### Descargas

| Asset | Descripcion |
|---|---|
| `forensic_suite.exe` | Ejecutable portable generado con PyInstaller |
| `forensic_suite_windows.zip` | Ejecutable + dependencias empaquetadas |
| `forensic_suite.exe.sha256` | Hash SHA-256 del ejecutable |
| `Source code (zip/tar.gz)` | Codigo fuente completo |

### Inicio rapido

1. Descarga `forensic_suite.exe`.
2. Ejecuta desde CMD o PowerShell:
   ```powershell
   forensic_suite.exe --help
   forensic_suite.exe hash evidencia.raw
   forensic_suite.exe memoria --analizar --dump memoria.raw -p windows.pslist
   ```

**Instrucciones completas:** [`docs/INSTALACION_WINDOWS.md`](docs/INSTALACION_WINDOWS.md)

### Caracteristicas de la version Windows

- Punto de entrada separado: `forensic_suite_windows/win_main.py`
- Capa de abstraccion Windows: `forensic_suite_windows/core/plataforma.py`
- Funciones disponibles: hash, manifest, acta, firma GPG, timestamp, carve, analyze, memoria --analizar (Volatility3), interact, listar discos, proteccion USB global.
- Limitaciones: bloqueo real por dispositivo y daemon no son equivalentes a Linux; adquisicion RAM requiere WinPmem/DumpIt.

---

## Verificacion de integridad

Cada release incluye archivos `.sha256`. Verifica con:

```bash
# Linux / macOS
sha256sum -c forensic-suite-live.iso.sha256

# Windows (PowerShell)
Get-FileHash forensic_suite.exe -Algorithm SHA256 | Select-Object Hash
```

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
