# Instalación en Windows

## Requisitos

- Windows 10/11 (64 bits).
- Python 3.9 o superior.
- PowerShell.
- (Opcional) Gpg4win para firmas GPG.

## Ejecutar desde código fuente (recomendado para pruebas)

```powershell
git clone https://github.com/tremolgraterol/forensicSuite.git
cd forensicSuite
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[full]"
pip install volatility3 pefile

forensic_suite.exe --help
forensic_suite.exe hash .\prueba.txt
```

## Empaquetar como ejecutable portable

```powershell
pip install pyinstaller
.\tools\build-windows.ps1
```

Salida: `dist\windows\forensic_suite\forensic_suite.exe`

Distribuye la **carpeta completa**; no muevas solo el `.exe`.

## Ejecutar un `.exe` sin firma (SmartScreen)

Windows bloquea ejecutables sin certificado de firma. Esto es normal.

### Opción A: Cuadro de diálogo
1. Doble clic en `forensic_suite.exe`.
2. En **"Windows protegió tu PC"**, pulsa **Más información** → **Ejecutar de todos modos**.

### Opción B: PowerShell
```powershell
Unblock-File -Path "dist\windows\forensic_suite\forensic_suite.exe"
```

### Opción C: Propiedades del archivo
1. Clic derecho → **Propiedades**.
2. Marca **Desbloquear** y acepta.

## Limitaciones en Windows

- `bloquear` / `desbloquear`: solo políticas de registro USB, no bloqueo por dispositivo.
- `daemon`: no disponible.
- `memoria --adquirir`: requiere herramientas externas como WinPmem o DumpIt.
- `listar`: usa PowerShell/WMI.

Para bloqueo forense real se recomienda usar el **USB Live forense**.

## Documentación completa

Ver [`docs/INSTALACION_WINDOWS.md`](https://github.com/tremolgraterol/forensicSuite/blob/main/docs/INSTALACION_WINDOWS.md).
