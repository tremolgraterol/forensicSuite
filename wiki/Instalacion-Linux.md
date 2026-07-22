# Instalación en Linux

## Requisitos

- Debian 12+, Ubuntu 22.04+, Kali o derivado.
- Python 3.9 o superior.
- Acceso a `sudo` para dependencias del sistema.

## Instalación automática

```bash
git clone https://github.com/tremolgraterol/forensicSuite.git
cd forensicSuite
sudo ./install.sh
```

## Instalación manual

```bash
sudo apt install hdparm util-linux gnupg openssl scalpel \
                 bulk-extractor python3-venv
python3 -m venv /opt/forensic_suite
source /opt/forensic_suite/bin/activate
pip install -e ".[full]"
```

## Crear USB/ISO Live forense

```bash
sudo apt install -y live-build debootstrap xorriso squashfs-tools
sudo ./tools/build-live-usb.sh

# Grabar en USB
lsblk
sudo dd if=forensic-suite-live.iso of=/dev/sdX bs=4M status=progress conv=fsync
```

> **Cuidado:** reemplaza `/dev/sdX` por tu USB. No uses el disco del sistema.

## Uso básico

```bash
forensic_suite --help
forensic_suite hash evidencia.raw
forensic_suite bloquear /dev/sdb
forensic_suite memoria --adquirir --salida memoria.lime
```

## Documentación completa

Ver [`docs/INSTALACION.md`](https://github.com/tremolgraterol/forensicSuite/blob/main/docs/INSTALACION.md) y [`docs/CREAR_USB_LIVE.md`](https://github.com/tremolgraterol/forensicSuite/blob/main/docs/CREAR_USB_LIVE.md).
