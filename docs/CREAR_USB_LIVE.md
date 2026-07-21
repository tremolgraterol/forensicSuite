# Crear USB/ISO Live con ForensicSuite

**Versión del documento:** 1.0  
**Última actualización:** 20 de julio de 2026

---

## ¿Qué es un entorno Live forense?

Un entorno **Live** es un sistema operativo completo que arranca desde USB/CD/DVD **sin instalar nada en el disco duro del equipo analizado**. Esto permite:

- No alterar la evidencia del disco interno.
- Bloquear el disco del anfitrión como evidencia.
- Tener todas las herramientas forenses listas.
- Garantizar cadena de custodia limpia.

---

## Opciones para crear el Live

| Método | Dificultad | Recomendado | Uso |
|--------|-----------|-------------|-----|
| Script `build-live-usb.sh` | Media | **Sí** | Genera ISO automáticamente con `live-build` |
| Cubic | Baja | Sí (GUI) | Personaliza ISO Ubuntu fácilmente |
| Manual persistente | Baja | Para pruebas | USB persistente donde instalas ForensicSuite a mano |

---

## Método 1: Script automático con live-build

### Requisitos

- Debian, Ubuntu o Kali actualizados.
- Acceso a root (`sudo`).
- Conexión a internet.
- Mínimo 20 GB libres en disco.

### Pasos

```bash
cd /home/tu_usuario/Documentos/EST_AN_FORENCE/forensic_suite

# 1. Instalar live-build si no lo tienes
sudo apt update
sudo apt install -y live-build debootstrap xorriso squashfs-tools

# 2. Ejecutar el script de construcción
sudo ./tools/build-live-usb.sh
```

El script hará:

1. Configurar `live-build` para Debian `trixie` amd64.
2. Incluir paquetes forenses disponibles en repositorios oficiales: `scalpel`, `dcfldd`, `gnupg`, `openssl`, `hdparm`, `sleuthkit`, `autopsy`, `foremost`, `binwalk`, `exiftool`, `gparted`, `cryptsetup`, `wireshark`, `tshark`, etc.
3. Instalar herramientas adicionales dentro de la ISO durante el build:
   - **Volatility3** (vía pip)
   - **AVML** (binario estático descargado de GitHub releases)
4. Copiar ForensicSuite a `/opt/forensic_suite` dentro del Live.
5. Instalar ForensicSuite automáticamente durante la construcción (la ISO ya la contiene lista).
6. Crear accesos directos en el escritorio.
7. Generar `forensic-suite-live.iso` en la raíz del proyecto.

**Nota sobre `bulk-extractor`:** actualmente no está disponible en los repositorios oficiales de Debian, por lo que no se incluye en la ISO. Si en el futuro vuelve a los repositorios, el script lo instalará automáticamente.

### Grabar en USB

```bash
# IDENTIFICA TU USB PRIMERO con lsblk. ¡NO uses el disco del sistema!
lsblk

# Grabar ISO en USB (reemplaza /dev/sdX por tu dispositivo USB)
sudo dd if=forensic-suite-live.iso of=/dev/sdX bs=4M status=progress conv=fsync
```

**⚠️ ATENCIÓN:** `of=/dev/sdX` borrará TODO el contenido del dispositivo. Asegúrate de que `/dev/sdX` sea el USB.

### Arrancar desde el USB Live

1. Inserta el USB en el equipo a analizar.
2. Enciende o reinicia el equipo.
3. Accede al menú de arranque (usualmente una de estas teclas): `F12`, `F10`, `F11`, `Esc`, `F2`.
4. Selecciona el dispositivo USB (puede aparecer como `UEFI: USB`, `USB-HDD` o la marca del USB).
5. Si el equipo no arranca, entra a la BIOS/UEFI y:
   - Desactiva temporalmente **Secure Boot**.
   - Asegúrate de que el modo **UEFI/Legacy (CSM)** permita arrancar desde USB.
6. El Live de Debian cargará ForensicSuite automáticamente.

---

## Método 2: Cubic (personalizar ISO Ubuntu)

1. Descarga una ISO Ubuntu o Kali.
2. Instala Cubic:
   ```bash
   sudo apt install -y cubic
   ```
3. Abre Cubic y selecciona la ISO original.
4. En el entorno chroot, ejecuta:
   ```bash
   apt update
   apt install -y hdparm util-linux dcfldd scalpel bulk-extractor gnupg openssl python3-venv python3-pip
   git clone https://github.com/tr3w01/forensic_suite.git /opt/forensic_suite
   cd /opt/forensic_suite
   ./install.sh --system
   ```
5. Finaliza Cubic y genera tu ISO personalizada.
6. Graba la ISO en USB con `dd` o balenaEtcher.

---

## Método 3: USB persistente manual (rápido para pruebas)

```bash
# 1. Descargar ISO Live de Debian/Ubuntu/Kali
# 2. Grabar en USB con persistencia (ejemplo con 8GB persistente)
sudo dd if=kali-linux.iso of=/dev/sdX bs=4M status=progress

# 3. Arrancar desde el USB y crear partición persistente (opcional)
# 4. Una vez dentro del Live:
sudo apt update
sudo apt install -y hdparm util-linux dcfldd scalpel bulk-extractor gnupg openssl python3-venv python3-pip git
git clone https://github.com/tr3w01/forensic_suite.git /opt/forensic_suite
cd /opt/forensic_suite
sudo ./install.sh
```

---

## Verificar el entorno Live

Después de arrancar desde el USB Live, abre una terminal y ejecuta:

```bash
forensic_suite --version
forensic_suite listar
```

Verifica que:

- El disco raíz detectado sea el **USB Live** (`/dev/sdb`, `/dev/sdc`, etc.).
- El disco interno del anfitrión aparezca como dispositivo bloqueable.

---

## Uso forense con Live USB

### Escenario típico

1. Equipo apagado → insertas USB Live forense.
2. Arrancas desde USB (puede requerir cambiar orden de arranque en BIOS/UEFI).
3. El sistema Live carga ForensicSuite.
4. El disco interno del anfitrión (ej: `/dev/sda`) **no es la raíz activa**.
5. Puedes bloquearlo como evidencia:
   ```bash
   sudo forensic_suite bloquear /dev/sda
   sudo forensic_suite listar
   ```

### ¿Por qué funciona?

La suite identifica como **disco raíz** el dispositivo desde el cual corre el sistema operativo **actual**. Cuando arrancas desde USB:

- Raíz = USB Live (`/dev/sdb`)
- Disco anfitrión = `/dev/sda` → puede bloquearse como evidencia

Si intentas bloquear el USB Live, la suite lo rechazará porque es la raíz activa.

---

## Seguridad

- **Nunca** grabes la ISO en el disco del sistema (`/dev/sda` en un equipo normal).
- **Siempre** verifica con `lsblk` antes de usar `dd`.
- Apaga el equipo analizado antes de insertar el USB Live para evitar alterar evidencia.
- En equipos con Windows, considera el apagado forzado si no puedes apagar limpiamente (evidencia volátil).

---

## Solución de problemas

### El equipo no arranca desde USB

- Entra a BIOS/UEFI con `F2`, `F10`, `F12` o `Del`.
- Desactiva **Secure Boot** temporalmente.
- Cambia el orden de arranque para priorizar USB.
- En UEFI, selecciona modo **Legacy/CSM** si es necesario.

### `live-build` no instala

```bash
sudo apt update
sudo apt install -y live-build debootstrap
```

### La ISO no cabe en DVD

Usa USB. Si necesitas DVD, reduce paquetes en `tools/build-live-usb.sh`.

---

## Referencias

- Debian Live: https://live-team.pages.debian.net/live-manual/
- Cubic: https://launchpad.net/cubic
- ForensicSuite README.md
