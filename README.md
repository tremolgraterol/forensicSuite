## ForensicSuite v2.0.0
Author: Alexander Graterol

Framework de Analisis Forense Digital con cadena de custodia MP 2017 y auditoría firmada.

![Build Windows](https://github.com/tremolgraterol/forensicSuite/actions/workflows/build-windows.yml/badge.svg)
[![Wiki](https://img.shields.io/badge/docs-Wiki-blue)](https://github.com/tremolgraterol/forensicSuite/wiki)
[![Discussions](https://img.shields.io/badge/discussions-Activas-green)](https://github.com/tremolgraterol/forensicSuite/discussions)

---

## Aviso legal y descargo de responsabilidad

Este proyecto tiene fines **exclusivamente educativos y de investigación académica** dentro del contexto del curso de **Informática Forense - Grupo Lazarus Venezuela**.

El autor y los colaboradores de ForensicSuite **no se hacen responsables** del uso indebido, malas prácticas, daños directos o indirectos, pérdida de información o consecuencias legales derivadas de la utilización de esta herramienta.

### Uso permitido

- Prácticas de laboratorio forense en entornos controlados.
- Análisis de equipos, discos o memorias sobre los que se cuente con autorización expresa.
- Formación académica en informática forense, ciberseguridad y auditoría de sistemas.

### Uso prohibido

- Acceder, examinar o extraer información de dispositivos sin autorización del titular.
- Utilizar la herramienta para ocultar, alterar, destruir o manipular evidencia digital.
- Cualquier actividad que vulnere la legislación vigente, incluyendo la **Ley Especial contra Delitos Informáticos de Venezuela** y el **Código Orgánico Procesal Penal**.

> **El uso responsable de esta herramienta es responsabilidad exclusiva del usuario.**

## Descargas

| Plataforma | Release | Asset principal |
|------------|---------|-----------------|
| Linux / Live USB | [v2.0.0-linux-live](https://github.com/tremolgraterol/forensicSuite/releases/tag/v2.0.0-linux-live) | `forensic-suite-live.iso` |
| Windows | [v2.0.0-windows](https://github.com/tremolgraterol/forensicSuite/releases/tag/v2.0.0-windows) | `forensic_suite.exe` |

Todas las releases incluyen hashes SHA-256 para verificar integridad.

## Instalacion

```bash
# Opcion 1: Instalador automatico (recomendado)
# Ejecutar como root para instalar dependencias del sistema (hdparm, scalpel, bulk-extractor, gnupg, openssl)
sudo ./install.sh

# Instalacion solo para el usuario (sin paquetes del sistema)
./install.sh --user

# Opcion 2: Manual (requiere python3-venv)
sudo apt install hdparm util-linux gnupg openssl scalpel bulk-extractor python3-venv
python3 -m venv /opt/forensic_suite
source /opt/forensic_suite/bin/activate
pip install -e .[full]

# Opcion 3: Symlink directo (sin pip)
ln -s "$(pwd)/forensic_suite/__main__.py" /usr/local/bin/forensic_suite
chmod +x /usr/local/bin/forensic_suite
```

El instalador `./install.sh` gestiona automaticamente:
- Dependencias del sistema via `apt` (`hdparm`, `scalpel`, `bulk-extractor`, `gnupg`, `openssl`, `python3-venv`).
- Virtualenv en `/opt/forensic_suite` y symlinks en `/usr/local/bin`.
- Bash completion para `forensic_suite` y `fs`.

Despues de instalar, ejecutar `forensic_suite` o `fs` (atajo) desde cualquier terminal.

---

## Crear USB/ISO Live forense

Para analizar equipos apagados sin alterar su disco interno, crea un **USB/ISO Live** con ForensicSuite preinstalada. Desde el Live, el disco interno del anfitrión no es la raíz del sistema y **sí se puede bloquear** como evidencia.

```bash
# Requisitos: live-build, debootstrap, root
sudo apt install -y live-build debootstrap xorriso squashfs-tools
sudo ./tools/build-live-usb.sh

# El script genera forensic-suite-live.iso basado en Debian 13 (trixie) amd64.
# Grabar en USB (reemplaza /dev/sdX por tu dispositivo USB)
sudo dd if=forensic-suite-live.iso of=/dev/sdX bs=4M status=progress conv=fsync
```

Documentación completa en `docs/CREAR_USB_LIVE.md`.

---

## Version Windows (experimental)

ForensicSuite puede empaquetarse como ejecutable `.exe` para Windows 10/11 usando PyInstaller.

La version Windows vive en su **propio directorio** (`forensic_suite_windows/`) con punto de entrada `forensic_suite_windows/win_main.py`, separado del Linux (`forensic_suite/__main__.py`).

```powershell
# En Windows, con Python 3.9+
pip install pyinstaller
.\tools\build-windows.ps1
```

**Funciones disponibles:** hash, manifest, acta, firma, timestamp, carve, memoria --analizar (Volatility3), interact.
**Limitaciones:** bloqueo de disco y daemon no son equivalentes a Linux; adquisicion de RAM requiere WinPmem/DumpIt.

Documentación completa en `docs/INSTALACION_WINDOWS.md`.

---

## Documentacion tecnica

La carpeta `docs/` contiene documentacion para auditores y contra peritos:

| Documento | Para quien |
|---|---|
| `docs/00_RESUMEN_EJECUTIVO.md` | Vision general |
| `docs/01_GUIA_USUARIO.md` | Perito que usa la herramienta |
| `docs/02_GUIA_TECNICA.md` | Detalle de implementacion |
| `docs/03_PROTOCOLO_FORENSE.md` | Protocolo paso a paso |
| `docs/04_VERIFICACION_CONTRA_PERITAJE.md` | Contra perito que verifica resultados |
| `docs/05_MARCO_LEGAL.md` | Fundamento legal Venezuela |
| `docs/06_VALIDACION_HERRAMIENTAS.md` | Auditor tecnico |
| `docs/CREAR_USB_LIVE.md` | Crear entorno Live forense |
| `docs/INSTALACION_WINDOWS.md` | Empaquetado y uso en Windows |

---

## Comandos

### Hashes - `forensic_suite hash`

Calcula SHA-256, SHA-512 y MD5 de un archivo en una sola pasada.

```bash
# Todos los hashes
forensic_suite hash evidence.raw

# Solo SHA-256
forensic_suite hash evidence.raw -a sha256

# Generar archivos .sha256/.sha512/.md5 y .hash consolidado
forensic_suite hash evidence.raw -g
```

Con `-g` se generan:
- `evidence.raw.sha256`
- `evidence.raw.sha512`
- `evidence.raw.md5`
- `evidence.raw.hash` (consolidado, firmado con GPG si hay clave configurada)

Todos los archivos se marcan como solo lectura (`444`) para preservar integridad.

### Verificar hash - `forensic_suite verificar`

Verifica que un archivo no fue modificado.

```bash
forensic_suite verificar evidence.raw a1b2c3d4e5... -a sha256
```

### Bloqueo de escritura - `forensic_suite bloquear`

Aplica protección contra escritura a nivel de kernel (`blockdev --setro`), loop device aislado y montaje forense endurecido. **Requiere root.**

```bash
sudo forensic_suite bloquear /dev/sdb
sudo forensic_suite desbloquear /dev/sdb
```

**Importante**: Esta herramienta utiliza bloqueo lógico por software. Para evidencia judicial que deba presentarse ante tribunales, se recomienda un **write blocker de hardware certificado** (ISO 27037). La verificación de bloqueo se realiza de forma pasiva (`blockdev --getro`, estado de montaje `ro`) sin intentar escribir en el dispositivo de evidencia.

### Listar dispositivos - `forensic_suite listar`

```bash
forensic_suite listar
forensic_suite listar -s    # incluir disco del sistema
```

### Acta de custodia - `forensic_suite acta`

Genera acta en formato MP 2017 (Markdown + JSON).

```bash
forensic_suite acta evidence.raw \
    --perito "Juan Perez" \
    --cedula "V-12345678" \
    --cargo "Perito en Informatica" \
    --caso "MP-2024-001" \
    --json

# Con transferencias
forensic_suite acta evidence.raw \
    --perito "Juan" \
    -t "Juan:Bodega:Resguardo" \
    -t "Bodega:Juez:Entrega judicial" \
    --cerrar "Archivo judicial" \
    --autoridad "Juez 5to" \
    --json
```

### Firma GPG - `forensic_suite firmar`

Genera firma detached (.asc).

```bash
forensic_suite firmar evidence.raw --key ABC123DEF456
forensic_suite verificar-firma evidence.raw
forensic_suite claves
```

### Sello de tiempo RFC 3161 - `forensic_suite timestamp`

```bash
# Obtener timestamp
forensic_suite timestamp evidence.raw
forensic_suite timestamp evidence.raw --tsa http://timestamp.digicert.com

# Verificar timestamp
forensic_suite verificar-timestamp evidence.raw.tsr
```

### Manifest JSON canonico - `forensic_suite manifest`

Genera manifest con hashes de todos los archivos de un directorio.

```bash
# Directorio completo
forensic_suite manifest /path/to/evidence/ --caso "MP-001" --perito "Juan"

# Solo archivos .raw
forensic_suite manifest /path/to/evidence/ -e ".raw,.dd,.img"

# Con verificacion inmediata
forensic_suite manifest /path/to/evidence/ -v

# Verificar un manifest existente
forensic_suite verificar-manifest /path/to/manifest.json
```

### Configuracion del perito - `forensic_suite perito`

```bash
forensic_suite perito --configurar    # interactivo
forensic_suite perito --ver           # ver configuracion actual
forensic_suite perito --info          # info del sistema
```

### Daemon de bloqueo automatico - `forensic_suite daemon`

```bash
forensic_suite daemon status          # ver modo detectado
sudo forensic_suite daemon install   # instalar servicio systemd + regla udev
sudo forensic_suite daemon uninstall # desinstalar y restaurar dispositivos a RW
```

**Comportamiento de la regla udev (seguro desde v2.0.0):**
- Detecta automáticamente el disco raíz del sistema operativo y lo **excluye** siempre.
- Solo bloquea discos completos conectados **después** del arranque (`ACTION=="add"`).
- No aplica `udevadm trigger` a dispositivos ya conectados, evitando bloquear el disco de arranque.
- El comando `uninstall` detiene el servicio, elimina la regla y restaura todos los dispositivos a lectura/escritura.

> **Aviso de seguridad**: versiones anteriores a la v2.0.0 podían bloquear el disco raíz al instalar el daemon. Si experimentaste este fallo, actualiza al código actual y usa `sudo forensic_suite daemon uninstall` para recuperar el sistema; si no arranca, sigue el procedimiento de recuperación con USB Live descrito en la documentación del daemon.

---

## Uso como modulo Python

```python
from forensic_suite.core.hasher import ForensicHasher
from forensic_suite.core.cadena_custodia import CadenaCustodia
from forensic_suite.core.manifest import ForensicManifest
from forensic_suite.core.firma_gpg import ForensicGPG
from forensic_suite.core.timestamp import ForensicTimestamp
from forensic_suite.core.perito import PeritoConfig
from forensic_suite.core.dispositivo import DispositivoForense

# Hashes
h = ForensicHasher()
r = h.calcular_todos("evidence.raw")
print(r.sha256, r.sha512, r.md5)

# Cadena de custodia
c = CadenaCustodia(
    archivo="evidence.raw",
    sha256=r.sha256,
    sha512=r.sha512,
    md5=r.md5,
    colector_nombre="Juan Perez",
    colector_cedula="V-12345678"
)
c.crear_acta("acta.chain")
c.agregar_transferencia("Juan", "Bodega", "Resguardo")
c.cerrar_cadena("Archivo judicial", "Juez 5to")
c.exportar_json("acta.json")

# Manifest
m = ForensicManifest()
m.escanear_directorio("/path/to/evidence/")
manifest = m.generar_manifest(caso_id="MP-001")
m.guardar(manifest, "manifest.json")
verif = m.verificar(manifest)

# Firma GPG
gpg = ForensicGPG(key_id="ABC123")
gpg.firmar("evidence.raw")
gpg.verificar("evidence.raw")

# Timestamp
ts = ForensicTimestamp()
ts.solicitar_timestamp("evidence.raw")
```

---

## Estructura del proyecto

```
forensic_suite/
├── forensic_suite/
│   ├── __init__.py
│   ├── __main__.py          # CLI
│   ├── core/
│   │   ├── dispositivo.py   # Bloqueo de escritura (NIVEL 0)
│   │   ├── hasher.py        # SHA-256/SHA-512/MD5
│   │   ├── perito.py        # Configuracion del perito
│   │   ├── cadena_custodia.py  # Acta MP 2017
│   │   ├── firma_gpg.py     # Firma digital GPG
│   │   ├── timestamp.py     # Sello RFC 3161
│   │   └── manifest.py      # Manifest JSON canonico
│   └── daemon/
│       ├── forensic_blockerd.py   # Daemon de bloqueo
│       ├── forensic-blockerd.service  # systemd
│       ├── 10-forensic-block.rules    # udev
│       └── forensic-block.conf        # config
├── tools/
│   └── build-live-usb.sh    # Script para construir ISO Live forense
├── tests/
│   └── test_suite.py        # 39 tests (incluye seguridad de daemon, permisos y Live/USB)
├── install.sh               # Instalador
├── setup.py
├── pyproject.toml
└── requirements.txt
```

---

## Entornos Live/USB y disco anfitrión

La suite **siempre** identifica como "disco raíz" el dispositivo desde el cual está corriendo el sistema operativo actual:

- **Sistema caliente (encendido normal)**: el disco interno es la raíz → `bloquear /dev/sda` se rechaza.
- **Sistema frío con USB Live**: el USB Live es la raíz (`/dev/sdb`) → el disco interno del anfitrión (`/dev/sda`) **sí se puede bloquear** como evidencia.

La detección reconoce entornos Live por:
- Puntos de montaje como `/run/live/medium`, `/cdrom`, `/run/initramfs/live`.
- Sistema de archivos raíz `overlay`, `squashfs`, `tmpfs`, `aufs`.
- Parámetros `boot=live`, `boot=casper`, `live-media` en `/proc/cmdline`.

## Recuperacion de emergencia (si el daemon bloqueo el disco raiz)

Si instalaste una version anterior del daemon y el sistema no arranca:

1. Arranca desde un USB Live.
2. Identifica tu disco raiz: `lsblk -f`
3. Desbloquea el disco:
   ```bash
   sudo blockdev --setrw /dev/sdX
   sudo hdparm -r0 /dev/sdX
   ```
4. Elimina la regla y el servicio:
   ```bash
   sudo rm /mnt/rescate/etc/udev/rules.d/10-forensic-block.rules
   sudo rm /mnt/rescate/etc/systemd/system/forensic-blockerd.service
   ```
5. Recarga reglas udev y reconstruye initramfs/GRUB.

Con la version actual (`>= 2.0.0`) basta con:
```bash
sudo forensic_suite daemon uninstall
```

---

## Advertencias forenses

- El bloqueo de escritura es **logico por software** (`blockdev --setro`, montaje `ro`). No sustituye a un write blocker de hardware certificado para cadena de custodia judicial formal.
- La verificacion de bloqueo es **pasiva**: nunca escribe en el dispositivo de evidencia para "probar" que esta bloqueado.
- La configuracion del perito se guarda con permisos `0o600` para proteger datos personales.

---

## Marco legal (Venezuela)

- **LECD** (G.O. 37.313): Delitos informaticos
- **COPP** Art. 183/187/224/225: Cadena de custodia y peritos
- **Ley de Mensajes de Datos**: Firmas electronicas
- **Manual MP 2017**: Formato de cadena de custodia

## Protocolos de referencia

- ISO 27037: Identification, collection, acquisition and preservation
- NIST SP 800-86: Guide to Integrating Forensic Techniques
- RFC 3161: Internet X.509 PKI Time-Stamp Protocol
- RFC 3227: Guidelines for Evidence Collection and Archiving

---

## Comunidad y soporte

- **Wiki**: https://github.com/tremolgraterol/forensicSuite/wiki
- **Discusiones**: https://github.com/tremolgraterol/forensicSuite/discussions
- **Reportar errores**: https://github.com/tremolgraterol/forensicSuite/issues

Usa las **Discussions** para preguntas generales, compartir experiencias o proponer mejoras. Usa **Issues** solo para reportar bugs.

---

Autor: Tr3w01 | Python 3.9+
