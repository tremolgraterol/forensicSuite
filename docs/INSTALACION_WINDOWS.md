# Instalacion de ForensicSuite en Windows

**Version del documento:** 1.0  
**Ultima actualizacion:** 21 de julio de 2026

---

## Resumen

ForensicSuite puede ejecutarse en **Windows 10/11** empaquetada como ejecutable portable (`forensic_suite.exe`).

**Directorios separados por plataforma:**

- Windows: `forensic_suite_windows/`
  - Punto de entrada: `forensic_suite_windows/win_main.py`
  - Capa Windows: `forensic_suite_windows/core/plataforma.py`
- Linux: `forensic_suite/`
  - Punto de entrada: `forensic_suite/__main__.py`

Asi se mantiene cada version totalmente independiente; el codigo Linux no depende de rutas ni bibliotecas de Windows, y viceversa.

**Funciones disponibles en Windows:**

- `hash` — calcular SHA-256, SHA-512, MD5 de archivos.
- `verificar` — verificar hashes.
- `manifest` / `verificar-manifest` — generar y verificar manifiestos.
- `acta` — generar acta de cadena de custodia.
- `timestamp` / `verificar-timestamp` — sellos de tiempo RFC 3161.
- `firmar` / `verificar-firma` — firmas GPG (requiere Gpg4win instalado).
- `perito` — configuracion del perito.
- `carve` / `analyze` — recuperacion de archivos con Scalpel (si esta en PATH).
- `memoria --analizar` — analisis de dumps RAM con **Volatility3**.
- `interact` — shell interactivo.

**Funciones con limitaciones en Windows:**

- `bloquear` / `desbloquear` — activan proteccion USB global via registro, **no** bloqueo por dispositivo como en Linux.
- `listar` — lista discos via PowerShell/WMI.
- `daemon` — no disponible (Windows no usa udev/systemd).
- `memoria --adquirir` — requiere herramientas externas: `WinPmem.exe` o `DumpIt.exe`.

> **Recomendacion para bloqueo forense real:** use el **USB Live forense** de ForensicSuite en lugar de la version Windows.

---

## Requisitos

- Windows 10 o Windows 11 (64 bits).
- Python 3.9 o superior.
- PowerShell.
- (Opcional) Gpg4win para firmas GPG.
- (Opcional) Volatility3 para analisis de memoria.

---

## Metodo 1: Ejecutar desde codigo fuente

Este es el metodo recomendado para validar ForensicSuite antes de generar o distribuir el ejecutable.

```powershell
# 1. Clonar el proyecto y entrar en su directorio
git clone https://github.com/tremolgraterol/forensicSuite.git
cd forensicSuite

# 2. Crear virtualenv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -e ".[full]"
pip install volatility3 pefile

# 4. Ejecutar el CLI exclusivo de Windows
python -m forensic_suite_windows.win_main --help

# 5. Prueba basica de hash
"prueba ForensicSuite" | Set-Content .\prueba.txt
python -m forensic_suite_windows.win_main hash .\prueba.txt
```

---

## Metodo 2: Empaquetar como ejecutable portable (PyInstaller)

```powershell
# 1. Instalar PyInstaller
pip install pyinstaller

# 2. Ejecutar el script de build
.\tools\build-windows.ps1

# Salida en: dist\windows\forensic_suite\forensic_suite.exe
```

El build se genera en formato **carpeta** (`onedir`) en `dist\windows\forensic_suite\`. Distribuye y ejecuta la carpeta completa; no muevas solo `forensic_suite.exe`, porque necesita sus dependencias junto a ella.

> No uses `-OneFile`: no es compatible con el archivo `forensic_suite.spec`. El formato por carpeta facilita pruebas y evita la compresion de binarios asociada a algunas alertas heuristicas.

## Pruebas locales y alertas de Microsoft Defender

Los ejecutables nuevos creados con PyInstaller y sin firma Authenticode pueden ser bloqueados por Microsoft Defender o Smart App Control con detecciones genericas, por ejemplo `Trojan:Win32/Sabsik.TE.A!ml`. Una deteccion heuristica no confirma por si sola que el proyecto tenga malware, pero el archivo debe verificarse antes de ejecutarse.

1. Prueba primero el codigo fuente con el **Metodo 1**.
2. Genera el ejecutable dentro de una VM Windows o equipo de laboratorio.
3. Calcula y conserva el hash del artefacto generado:

   ```powershell
   Get-FileHash .\dist\windows\forensic_suite\forensic_suite.exe -Algorithm SHA256
   ```

4. Ejecuta las pruebas funcionales desde el codigo fuente y, si Defender permite el binario, desde el ejecutable:

   ```powershell
   python -m unittest tests.test_suite
   python -m forensic_suite_windows.win_main --help
   python -m forensic_suite_windows.win_main memoria --verificar-entorno
   ```

5. No desactives Microsoft Defender ni Smart App Control en un equipo de produccion para ignorar una alerta.
6. Antes de distribuir el `.exe` a terceros, firmalo con un certificado Code Signing y publica su hash SHA-256 en el release.

La ejecucion desde codigo fuente permite validar la aplicacion aunque un `.exe` descargado sin firma sea bloqueado. La distribucion publica de binarios sin firma no se recomienda.

---

## Uso basico en Windows

```powershell
# Hashes
forensic_suite.exe hash evidencia.raw

# Manifiesto
forensic_suite.exe manifest C:\Evidencia\caso001 -o manifest.json

# Analizar memoria (dump adquirido previamente con WinPmem)
forensic_suite.exe memoria --analizar --dump C:\Evidencia\memoria.raw -p windows.pslist

# Shell interactivo
forensic_suite.exe interact
```

---

## Herramientas externas recomendadas

| Funcion | Herramienta Windows | URL |
|---|---|---|
| Firma GPG | Gpg4win | https://www.gpg4win.org |
| Dump RAM | WinPmem | https://github.com/Velocidex/WinPmem |
| Dump RAM | Magnet RAM Capture | https://www.magnetforensics.com |
| Carving | Scalpel para Windows | Compilar desde fuentes |

---

## Limitaciones conocidas

1. **Bloqueo de disco:** Windows no expone `/dev/sdX` ni `blockdev`. El comando `bloquear` solo activa politicas de registro USB. Para bloqueo real usar hardware o Live USB.
2. **Daemon:** no se instala servicio de bloqueo automatico en Windows.
3. **Adquisicion RAM:** no se incluye un volcador de memoria nativo. Se requiere WinPmem/DumpIt.

---

## Solucion de problemas

### `forensic_suite.exe` no se encuentra

Agrega la carpeta `dist\windows\forensic_suite` al PATH o usa la ruta completa.

### Volatility3 no funciona

```powershell
pip install volatility3 pefile
```

### GPG no funciona

Instala Gpg4win y reinicia la terminal:

```powershell
choco install gpg4win
# o descarga desde https://www.gpg4win.org
```

---

## Referencias

- `forensic_suite.spec` — especificacion de PyInstaller.
- `tools/build-windows.ps1` — script de construccion.
- `forensic_suite_windows/win_main.py` — punto de entrada CLI Windows.
- `forensic_suite_windows/core/plataforma.py` — capa de abstraccion Windows.
- `docs/CREAR_USB_LIVE.md` — version completa en Live USB.
