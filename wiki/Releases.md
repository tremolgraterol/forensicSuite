# Releases de ForensicSuite

## Descargas oficiales

| Plataforma | Tag | Asset principal | Notas |
|------------|-----|-----------------|-------|
| Linux / Live USB | [v2.0.0-linux-live](https://github.com/tremolgraterol/forensicSuite/releases/tag/v2.0.0-linux-live) | `forensic-suite-live.iso` | Arranque forense basado en Debian 13. |
| Windows | [v2.0.0-windows](https://github.com/tremolgraterol/forensicSuite/releases/tag/v2.0.0-windows) | `forensic_suite.exe` | Ejecutable portable generado con PyInstaller. |

Cada release incluye un archivo `.sha256` para verificar integridad.

## Verificar integridad

### Linux

```bash
sha256sum -c forensic-suite-live.iso.sha256
```

### Windows

```powershell
Get-FileHash forensic_suite.exe -Algorithm SHA256
# Comparar con el valor del archivo .sha256
```

## Build automático

El ejecutable Windows se compila automáticamente con GitHub Actions cada vez que se publica un tag que contenga `windows`.

Ver workflow: `.github/workflows/build-windows.yml`

## Historial

| Versión | Fecha | Cambios |
|---------|-------|---------|
| v2.0.0 | 2026-07-21 | Primera release pública: Linux Live USB + Windows portable. |

Ver [`RELEASES.md`](https://github.com/tremolgraterol/forensicSuite/blob/main/RELEASES.md) para más detalles.
