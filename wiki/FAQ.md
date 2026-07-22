# Preguntas frecuentes (FAQ)

## ¿Es gratis?

Sí. ForensicSuite es un proyecto educativo y de código abierto.

## ¿Puedo usarlo en producción?

El proyecto está pensado para **formación académica y laboratorios controlados**. Para uso profesional verifica la cadena de custodia, firma los binarios y audita el código.

## ¿Por qué Windows bloquea el `.exe`?

PyInstaller genera ejecutables sin firma digital. Windows 10/11 muestra **SmartScreen** o **Defender** para archivos de origen desconocido. Esto no significa que tenga malware.

Soluciones:
- Pulsa **Más información** → **Ejecutar de todos modos**.
- Usa `Unblock-File` en PowerShell.
- Marca **Desbloquear** en las propiedades del archivo.

Para distribución pública se recomienda un certificado **Authenticode**.

## `forensic_suite.exe listar` dice `lsblk` no encontrado

Eso pasa si ejecutas el CLI de Linux en Windows. Asegúrate de:
1. Haber actualizado el repo: `git pull origin main`.
2. Reinstalar el paquete: `pip install -e ".[full]"`.
3. Usar `forensic_suite.exe` en Windows, que ahora redirige automáticamente al CLI Windows.

## `build-windows.ps1` pide ejecutar como administrador

Tienes una versión vieja del script. Actualiza el repo:

```powershell
git pull origin main
```

La versión actual no requiere administrador.

## ¿Cómo instalo Volatility3?

```bash
# Linux
pip install volatility3 pefile

# Windows
pip install volatility3 pefile
```

## ¿Cómo genero el USB Live forense?

```bash
sudo apt install -y live-build debootstrap xorriso squashfs-tools
sudo ./tools/build-live-usb.sh
```

Luego graba la ISO en USB con `dd`.

## ¿Dónde reporto errores?

Abre un **Issue** en el repositorio:

```text
https://github.com/tremolgraterol/forensicSuite/issues
```
