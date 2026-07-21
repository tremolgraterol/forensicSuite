# GUIA DE INSTALACION - ForensicSuite v2.0.0

**Version del documento:** 2.0  
**Ultima actualizacion:** 20 de julio de 2026  
**Objetivo:** Documentacion completa del proceso de instalacion para auditoria y transparencia

---

## INDICE

1. [Resumen de componentes](#1-resumen-de-componentes)
2. [Requisitos previos](#2-requisitos-previos)
3. [Metodos de instalacion](#3-metodos-de-instalacion)
4. [Que se instala y donde](#4-que-se-instala-y-donde)
5. [Dependencias y versiones](#5-dependencias-y-versiones)
6. [Herramientas del sistema](#6-herramientas-del-sistema)
7. [Verificar instalacion](#7-verificar-instalacion)
8. [Desinstalacion](#8-desinstalacion)
9. [Entornos Live/USB y recuperacion](#9-entornos-liveusb-y-recuperacion)
10. [Solucion de problemas](#10-solucion-de-problemas)
11. [Politica de versiones](#11-politica-de-versiones)

---

## 1. RESUMEN DE COMPONENTES

ForensicSuite consta de 4 componentes principales:

| Componente | Descripcion | Ubicacion |
|------------|-------------|-----------|
| **CLI** | Interfaz de comandos (forensic_suite/fs) | `~/.local/bin/forensic_suite` |
| **Core** | Modulos Python del framework | `forensic_suite/forensic_suite/core/` |
| **Daemon** | Servicio de bloqueo automatico | `/etc/systemd/system/forensic-blockerd.service` |
| **Configs** | Perfiles de carving y reglas udev | `forensic_suite/configs/` |

---

## 2. REQUISITOS PREVIOS

### 2.1 Sistema Operativo

| SO | Soporte | Notas |
|----|---------|-------|
| Linux (Debian/Ubuntu) | Completo | Recomendado |
| Linux (RHEL/CentOS) | Parcial | Requiere `dnf` en vez de `apt` |
| Windows (WSL2) | Parcial | Sin bloqueo hdparm |
| Windows (nativo) | Limitado | Sin bloqueo de escritura |

### 2.2 Python

**Version minima:** Python 3.9  
**Version recomendada:** Python 3.11 o 3.12

```bash
# Verificar version
python3 --version

# Si no tienes Python 3.9+
sudo apt update
sudo apt install python3 python3-pip python3-venv python3-psutil
```

### 2.3 Herramientas del sistema (gestionadas por install.sh)

El instalador `./install.sh` ejecutado como root instala automaticamente los paquetes esenciales via `apt`. Para instalacion manual:

| Herramienta | Para que sirve | Instalar |
|-------------|----------------|----------|
| `hdparm` | Bloqueo firmware ATA (legacy/opcional) | `sudo apt install hdparm` |
| `blockdev` / `findmnt` / `lsblk` | Bloqueo kernel, deteccion de disco raiz | `sudo apt install util-linux` |
| `dcfldd` | Clonado forense con hash | `sudo apt install dcfldd` |
| `scalpel` | Recuperacion archivos | `sudo apt install scalpel` |
| `bulk-extractor` | Extraccion masiva de artefactos | `sudo apt install bulk-extractor` |
| `gpg` | Firma digital | `sudo apt install gnupg` |
| `openssl` | Timestamps RFC 3161 | `sudo apt install openssl` |
| `losetup` | Loop devices | `sudo apt install util-linux` |
| `mtools` | Manipulacion FAT | `sudo apt install mtools` |

```bash
# Instalar todas las herramientas recomendadas
sudo apt install hdparm util-linux dcfldd scalpel bulk-extractor gnupg openssl mtools
```

---

## 3. METODOS DE INSTALACION

### 3.1 Instalador automatico (recomendado)

```bash
# Clonar o descargar el proyecto
git clone https://github.com/tr3w01/forensic_suite.git
cd forensic_suite

# Ejecutar instalador
./install.sh
```

**El instalador automatico hace:**
1. Detecta Python 3.9+
2. Instala dependencias del sistema via `apt` (si se ejecuta como root): `hdparm`, `util-linux`, `gnupg`, `openssl`, `scalpel`, `bulk-extractor`, `python3-venv`
3. Crea virtualenv en `~/.local/` o `/opt/forensic_suite/`
4. Instala dependencias Python via pip incluyendo extras `full`
5. Crea binarios `forensic_suite` y `fs` en PATH
6. Configura bash completion
7. Agrega PATH a `.bashrc` si es necesario

### 3.2 Instalacion manual

```bash
# 1. Instalar dependencias del sistema
sudo apt update
sudo apt install hdparm util-linux dcfldd scalpel bulk-extractor gnupg openssl python3-venv

# 2. Crear entorno virtual
python3 -m venv ~/forensic_venv

# 3. Activar
source ~/forensic_venv/bin/activate

# 4. Instalar la suite en modo desarrollo con extras completos
pip install -e /ruta/a/forensic_suite/[full]

# 5. Verificar
forensic_suite --version
```

### 3.3 Instalacion sin pip (symlink directo)

```bash
# Crear symlink directo al script
sudo ln -s /ruta/a/forensic_suite/forensic_suite/__main__.py /usr/local/bin/forensic_suite
sudo chmod +x /usr/local/bin/forensic_suite

# Crear atajo
sudo ln -s /usr/local/bin/forensic_suite /usr/local/bin/fs
```

**Limitacion:** No instala dependencias Python automaticamente.

---

## 4. QUE SE INSTALA Y DONDE

### 4.1 Archivos de la suite

| Archivo/Directorio | Ubicacion | Descripcion |
|--------------------|-----------|-------------|
| `forensic_suite/` | Directorio del proyecto | Paquete Python principal |
| `forensic_suite/core/` | `forensic_suite/core/` | Modulos: dispositivo, hasher, cadena_custodia, firma_gpg, timestamp, manifest, scalpel, memoria, perito |
| `forensic_suite/daemon/` | `forensic_suite/daemon/` | forensic_blockerd.py, mforense |
| `forensic_suite/configs/` | `forensic_suite/configs/` | Perfiles de carving: recuperacion.conf, cripto.conf, medios.conf, documentos.conf, redes.conf, general.conf |
| `__main__.py` | `forensic_suite/__main__.py` | Punto de entrada CLI |
| `pyproject.toml` | Raiz del proyecto | Configuracion de build |
| `install.sh` | Raiz del proyecto | Instalador automatico |

### 4.2 Archivos generados en el sistema

| Archivo | Ubicacion | Cuando se crea |
|---------|-----------|----------------|
| `forensic_suite` (binario) | `~/.local/bin/forensic_suite` | Instalacion |
| `fs` (atajo) | `~/.local/bin/fs` | Instalacion |
| Bash completion | `~/.local/share/bash-completion/completions/forensic_suite` | Instalacion |
| Config perito | `~/.forensic_suite/perito.conf` | `forensic_suite perito --configurar` |
| Archivos .sha256, .sha512, .md5 | Directorio del archivo hasheado | `forensic_suite hash -g` |
| Archivo .hash consolidado | Directorio del archivo hasheado | `forensic_suite hash -g` |
| Archivos .sig (GPG) | Directorio del archivo hasheado | Generado automaticamente con hash -g si hay clave GPG |
| Actas custodia | Directorio del caso | `forensic_suite acta` |
| Imagenes forenses | Directorio del caso | `dcfldd` o `forensic_suite clone` |

### 4.3 Archivos del daemon (instalacion global)

| Archivo | Ubicacion | Descripcion |
|---------|-----------|-------------|
| Servicio systemd | `/etc/systemd/system/forensic-blockerd.service` | Servicio del daemon |
| Script daemon | `/opt/forensic_suite/forensic_blockerd.py` | Codigo del daemon |
| Regla udev | `/etc/udev/rules.d/10-forensic-block.rules` | Deteccion USB |
| Config daemon | `/etc/forensic-blockerd.conf` | Configuracion |

---

## 5. DEPENDENCIAS Y VERSIONES

### 5.1 Dependencias Python (instaladas via pip)

| Paquete | Version minima | Version recomendada | Obligatorio | Proposito |
|---------|----------------|---------------------|-------------|-----------|
| `psutil` | >=5.9.0 | 5.9.8 | SI | Informacion de procesos y sistemas |
| `cryptography` | >=41.0.0 | 42.0.0 | NO | Firma GPG y encriptacion |
| `requests` | >=2.28.0 | 2.31.0 | NO | Requests HTTP (timestamps) |

```bash
# Verificar versiones instaladas
pip list | grep -E "psutil|cryptography|requests"
```

### 5.2 Dependencias del sistema (gestionadas por install.sh si se ejecuta como root)

| Paquete | Version minima | Comando verificar | Paquete apt |
|---------|----------------|-------------------|-------------|
| `python3` | 3.9 | `python3 --version` | `python3` |
| `hdparm` | 9.58 | `hdparm -V` | `hdparm` |
| `blockdev` / `findmnt` / `lsblk` | 2.38 | `blockdev --version` | `util-linux` |
| `dcfldd` | 1.9 | `dcfldd -V` | `dcfldd` |
| `scalpel` | 1.60 | `scalpel -v` | `scalpel` |
| `bulk-extractor` | (segun repo) | `bulk_extractor -V` | `bulk-extractor` |
| `gpg` | 2.2 | `gpg --version` | `gnupg` |
| `openssl` | 1.1.1 | `openssl version` | `openssl` |
| `losetup` | 2.38 | `losetup --version` | `util-linux` |
| `sha256sum` | 8.32 | `sha256sum --version` | `coreutils` |
| `md5sum` | 8.32 | `md5sum --version` | `coreutils` |

---

## 6. HERRAMIENTAS DEL SISTEMA

ForensicSuite **usa** estas herramientas. Desde la v2.0.0, `install.sh` ejecutado como root las instala automaticamente via `apt`.

### 6.1 Bloqueo de escritura

| Herramienta | Uso en la suite | Comando equivalente |
|-------------|-----------------|---------------------|
| `hdparm` | Bloqueo firmware ATA (legacy/opcional) | `hdparm -r1 /dev/sdX` |
| `blockdev` | Bloqueo kernel block layer | `blockdev --setro /dev/sdX` |
| `findmnt` | Verificar montaje solo lectura | `findmnt -n -o OPTIONS /dev/sdX` |
| `losetup` | Loop device read-only | `losetup --partscan --show -r -f /dev/sdX` |
| `mount` | Montaje solo lectura | `mount -o ro,loop,noexec,nodev /dev/sdX /mnt` |

> **Nota:** `hdparm -r1` no funciona en USB/NVMe/SSD modernos. La suite lo usa como capa adicional opcional; el bloqueo principal es `blockdev --setro`.

### 6.2 Clonado forense

| Herramienta | Uso en la suite | Comando equivalente |
|-------------|-----------------|---------------------|
| `dcfldd` | Clonado con hash integrado | `dcfldd if=/dev/sdX of=imagen.raw bs=4M hash=sha256` |
| `dd` | Clonado basico (fallback) | `dd if=/dev/sdX of=imagen.raw bs=4M status=progress` |

### 6.3 Carving y extraccion de artefactos

| Herramienta | Uso en la suite | Comando equivalente |
|-------------|-----------------|---------------------|
| `scalpel` | Recuperacion de archivos eliminados por firmas | `scalpel -o salida imagen.raw` |
| `bulk_extractor` | Extraccion masiva de artefactos (emails, URLs, tarjetas, etc.) | `bulk_extractor -o salida imagen.raw` |

### 6.4 Firma y timestamp

| Herramienta | Uso en la suite | Comando equivalente |
|-------------|-----------------|---------------------|
| `gpg` | Firma detached de evidencia | `gpg --detach-sign archivo` |
| `openssl` | Timestamp RFC 3161 | `openssl ts -query -data archivo -sha256 -out request.tsq` |

### 6.5 Memoria forense

| Herramienta | Uso en la suite | Notas |
|-------------|-----------------|-------|
| `mforense` | Adquisicion RAM | Incluido en `daemon/mforense` |
| `/proc/kcore` | Dump memoria via kernel | Requiere root |
| `lime` | Kernel module dump | Opcional, no incluido |

---

## 7. VERIFICAR INSTALACION

### 7.1 Verificacion basica

```bash
# Verificar que el comando existe
which forensic_suite
which fs

# Verificar version
forensic_suite --version
# Salida esperada: ForensicSuite 2.0.0

# Verificar help
forensic_suite --help
```

### 7.2 Verificar dependencias Python

```bash
# Verificar que importa correctamente
python3 -c "import forensic_suite; print('OK')"

# Verificar psutil
python3 -c "import psutil; print(f'psutil {psutil.__version__}')"
```

### 7.3 Verificar herramientas del sistema

```bash
# Script de verificacion completa
echo "=== Verificando ForensicSuite ==="
echo ""

echo "1. Python:"
python3 --version

echo "2. ForensicSuite:"
forensic_suite --version

echo "3. Herramientas del sistema:"
for cmd in hdparm blockdev findmnt dcfldd scalpel bulk_extractor gpg openssl losetup sha256sum md5sum; do
    if command -v $cmd &>/dev/null; then
        echo "  [OK] $cmd"
    else
        echo "  [FALTA] $cmd"
    fi
done

echo "4. Bash completion:"
if [ -f ~/.local/share/bash-completion/completions/forensic_suite ]; then
    echo "  [OK] Completion instalado"
else
    echo "  [FALTA] Completion no encontrado"
fi

echo "5. PATH:"
if echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo "  [OK] ~/.local/bin en PATH"
else
    echo "  [WARN] ~/.local/bin NO en PATH"
fi
```

### 7.4 Verificar modulos internos

```bash
# Test de cada modulo core
python3 -c "
from forensic_suite.core.dispositivo import verificar_entorno_forense
from forensic_suite.core.hasher import ForensicHasher
from forensic_suite.core.cadena_custodia import CadenaCustodia
from forensic_suite.core.firma_gpg import ForensicGPG
from forensic_suite.core.timestamp import ForensicTimestamp
from forensic_suite.core.manifest import ForensicManifest
from forensic_suite.core.scalpel import ForensicScalpel
from forensic_suite.core.memoria import ForensicMemoria
print('Todos los modulos importados correctamente')
"

# Ejecutar suite completa de tests
python3 -m unittest tests.test_suite -v
```

---

## 8. DESINSTALACION

### 8.1 Desinstalacion completa

```bash
# 1. Desinstalar paquete Python
pip uninstall forensic-suite

# 2. Eliminar binarios
rm ~/.local/bin/forensic_suite
rm ~/.local/bin/fs

# 3. Eliminar completion
rm ~/.local/share/bash-completion/completions/forensic_suite

# 4. Eliminar de .bashrc
sed -i '/ForensicSuite/d' ~/.bashrc
sed -i '/forensic_suite/d' ~/.bashrc

# 5. Eliminar configuracion del perito
rm ~/.forensic_perito.json

# 6. Eliminar archivos generados (opcional)
# CUIDADO: elimina evidencia forense
# rm -rf ~/forense_practica/

echo "ForensicSuite desinstalado"
```

### 8.2 Desinstalar daemon (si se instalo)

```bash
# Forma recomendada desde v2.0.0: desinstala, elimina reglas y restaura dispositivos a RW
sudo forensic_suite daemon uninstall
```

Si prefieres hacerlo manualmente:

```bash
# Detener servicio
sudo systemctl stop forensic-blockerd

# Deshabilitar
sudo systemctl disable forensic-blockerd

# Eliminar archivos
sudo rm /etc/systemd/system/forensic-blockerd.service
sudo rm /etc/udev/rules.d/10-forensic-block.rules
sudo rm /etc/forensic_suite/forensic-block.conf
sudo rm -rf /opt/forensic_suite

# Recargar systemd y udev
sudo systemctl daemon-reload
sudo udevadm control --reload-rules

# Restaurar dispositivos a lectura/escritura
for dev in /dev/sd* /dev/nvme*; do
    [ -b "$dev" ] && sudo blockdev --setrw "$dev"
done
```

### 8.3 Desinstalacion local (sin sudo)

```bash
# Eliminar solo archivos del usuario
rm -rf ~/.local/bin/forensic_suite
rm -rf ~/.local/bin/fs
rm -rf ~/.local/share/bash-completion/completions/forensic_suite
pip uninstall forensic-suite
```

## 9. ENTORNOS LIVE/USB Y RECUPERACION

### 9.1 Entornos Live/USB y disco anfitrión

La suite detecta como "disco raíz" el dispositivo desde el cual corre el sistema operativo actual:

- **Sistema encendido normalmente (caliente)**: el disco interno es la raíz. `forensic_suite bloquear /dev/sda` se rechaza.
- **Arranque desde USB Live (frío)**: el USB Live es la raíz (`/dev/sdb`). El disco interno del anfitrión (`/dev/sda`) **puede bloquearse** como evidencia, porque ya no es la raíz activa.

La detección de entorno Live usa:
- Puntos de montaje típicos (`/run/live/medium`, `/cdrom`, `/run/initramfs/live`).
- Sistema de archivos raíz `overlay`, `squashfs`, `tmpfs`, `aufs`.
- Parámetros de arranque (`boot=live`, `boot=casper`, `live-media`, `liveimg`).

### 9.2 Recuperacion de emergencia (disco raiz bloqueado)

Si una version anterior del daemon bloqueo el disco raiz y el sistema no arranca:

1. Arrancar desde USB Live.
2. Identificar el disco raiz: `lsblk -f`
3. Desbloquear desde el Live:
   ```bash
   sudo blockdev --setrw /dev/sdX
   sudo hdparm -r0 /dev/sdX
   ```
4. Montar el sistema y eliminar la regla udev/servicio:
   ```bash
   sudo mount /dev/sdX2 /mnt/rescate
   sudo rm /mnt/rescate/etc/udev/rules.d/10-forensic-block.rules
   sudo rm /mnt/rescate/etc/systemd/system/forensic-blockerd.service
   ```
5. Reconstruir initramfs/GRUB (ver seccion completa en README.md).

Con la version actual (`>= 2.0.0`) esto no deberia ocurrir porque la regla udev excluye automaticamente el disco raiz.

---

## 10. SOLUCION DE PROBLEMAS

### 10.1 "forensic_suite: command not found"

**Causa:** `~/.local/bin` no esta en PATH

```bash
# Solucion 1: Agregar a PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Solucion 2: Usar ruta completa
~/.local/bin/forensic_suite --version
```

### 10.2 "ModuleNotFoundError: No module named 'forensic_suite'"

**Causa:** No se instalo en modo desarrollo

```bash
# Reinstalar en modo editable
pip install -e /ruta/a/forensic_suite/

# O agregar ruta al PYTHONPATH
export PYTHONPATH="/ruta/a/forensic_suite:$PYTHONPATH"
```

### 10.3 "pip no encuentra psutil"

```bash
# Instalar psutil manualmente
pip install psutil>=5.9.0

# O usar pip del sistema
sudo pip3 install psutil>=5.9.0
```

### 10.4 "hdparm: command not found"

```bash
# Instalar hdparm
sudo apt install hdparm

# Verificar que funciona
sudo hdparm -I /dev/sda | head -5
```

### 10.5 "Permission denied" al bloquear

```bash
# Ejecutar con sudo
sudo forensic_suite bloquear /dev/sdX

# O agregar usuario al grupo disk
sudo usermod -aG disk $USER
# Cerrar sesion y volver a entrar
```

### 10.6 Bash completion no funciona

```bash
# Recargar completion
source ~/.local/share/bash-completion/completions/forensic_suite

# O recargar bash completo
exec bash
```

---

## 11. POLITICA VERSIONES

### 11.1 Numeracion de versiones

ForensicSuite usa versionado **Semantico** (Semantic Versioning):

```
MAJOR.MINOR.PATCH

MAJOR: Cambios incompatibles con versiones anteriores
MINOR: Nuevas funcionalidades compatibles hacia atras
PATCH: Correccion de bugs
```

**Version actual:** 2.0.0

### 11.2 Como se manejan las actualizaciones

| Tipo de instalacion | Actualizacion |
|---------------------|---------------|
| `pip install -e .` | `git pull && pip install -e .` |
| Symlink directo | `git pull` (se actualiza automaticamente) |
| Instalador | Ejecutar `./install.sh` nuevamente |

### 11.3 Compatibilidad

| Version Python | Soportado |
|----------------|-----------|
| 3.9 | SI |
| 3.10 | SI |
| 3.11 | SI (recomendado) |
| 3.12 | SI |
| 3.13 | SI (probar) |
| <3.9 | NO |

### 11.4 Registro de cambios (CHANGELOG)

#### v2.0.0
- **Deteccion de disco raiz**: mejora en `dispositivo.py` y `forensic_blockerd.py` para soportar particiones, LVM, LUKS, RAID, NVMe y entornos Live/USB.
- **Entornos Live/USB**: el disco raíz detectado es el medio Live (USB), permitiendo bloquear el disco interno del anfitrión como evidencia.
- **Seguridad del bloqueo**: el CLI y la API rechazan bloquear el dispositivo desde el cual corre el sistema operativo actual, ya sea en arranque normal o Live USB.
- **Seguridad del daemon**: la regla udev excluye automaticamente el disco raiz detectado.
- **Regla udev**: solo bloquea discos completos conectados despues del arranque (`ACTION=="add"`); no aplica `udevadm trigger` a dispositivos ya conectados.
- **Verificacion de bloqueo**: eliminada la prueba destructiva `dd if=/dev/zero`; ahora es pasiva (`blockdev --getro`, montaje `ro`).
- **Hash**: `forensic_suite hash -g` genera archivos individuales `.sha256`, `.sha512`, `.md5` mas `.hash` consolidado.
- **Permisos**: `perito.conf` se guarda con permisos `0o600`.
- **Dependencias**: `install.sh` instala automaticamente `hdparm`, `util-linux`, `gnupg`, `openssl`, `scalpel`, `bulk-extractor` y `python3-venv`.
- **Tests**: suite ampliada a 39 tests incluyendo seguridad del daemon, permisos y bloqueo del disco raiz.

```bash
# Ver historial de versiones
git log --oneline -20

# Ver cambios entre versiones
git diff v1.0.0..v2.0.0
```

---

## APENDICE A: ESTRUCTURA COMPLETA DE ARCHIVOS

```
forensic_suite/
├── forensic_suite/
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── dispositivo.py   # Bloqueo de escritura
│   │   ├── hasher.py        # SHA-256/512/MD5
│   │   ├── cadena_custodia.py  # Actas MP 2017
│   │   ├── firma_gpg.py     # Firma digital
│   │   ├── timestamp.py     # RFC 3161
│   │   ├── manifest.py      # Manifest JSON
│   │   ├── scalpel.py       # Carving wrapper
│   │   ├── memoria.py       # mforense wrapper
│   │   └── perito.py        # Config perito
│   ├── daemon/
│   │   ├── forensic_blockerd.py  # Daemon bloqueo
│   │   ├── forensic-blockerd.service
│   │   ├── forensic-block.conf
│   │   ├── 10-forensic-block.rules
│   │   └── mforense         # Memory forensics v2.5.0
│   └── configs/
│       ├── recuperacion.conf
│       ├── cripto.conf
│       ├── medios.conf
│       ├── documentos.conf
│       ├── redes.conf
│       └── general.conf
├── docs/                    # Documentacion
├── tests/                   # Pruebas unitarias
├── install.sh               # Instalador
├── pyproject.toml           # Config build
├── setup.py                 # Setup legacy
└── README.md
```

---

## APENDICE B: VERIFICACION PARA CONTRA-PERITAJE

Para verificar que la instalacion es legitima en un proceso judicial:

1. **Verificar hash del codigo fuente:**
```bash
cd forensic_suite
sha256sum -c checksums.sha256
```

2. **Verificar que no hay codigo malicioso:**
```bash
# Buscar conexiones de red sospechosas
grep -r "socket\|requests.post\|urllib" forensic_suite/

# Buscar escritura de archivos fuera de contexto
grep -r "open(\|write(" forensic_suite/core/ | grep -v "\.hash\|\.json\|\.md"
```

3. **Verificar firmas GPG del proyecto:**
```bash
git verify-commit HEAD
```

4. **Auditar dependencias:**
```bash
pip list --format=json > instalacion_actual.json
diff instalacion_actual.json dependencias_oficiales.json
```

---

**FIN DEL DOCUMENTO**

Para soporte: https://github.com/tr3w01/forensic_suite/issues
