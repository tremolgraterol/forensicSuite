#!/bin/bash
# build-live-usb.sh - Construye una ISO Live de Debian con ForensicSuite preinstalada
# =================================================================================
# Requiere: root, debian-based host, live-build, debootstrap
# Uso: sudo ./tools/build-live-usb.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_DIR="${PROJECT_DIR}/live-build"
ISO_OUTPUT="${PROJECT_DIR}/forensic-suite-live.iso"

# Distribución base. Puedes cambiar a "trixie", "bookworm", "bullseye", "kali-last-snapshot", etc.
DEBIAN_DIST="trixie"
ARCH="amd64"

error() {
    echo -e "${RED}ERROR:${NC} $1" >&2
    exit 1
}

info() {
    echo -e "${CYAN}[INFO]${NC} $1"
}

ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# ─────────────────────────────────────────────────────────────
# 1. Verificar root
# ─────────────────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    error "Este script debe ejecutarse como root. Ejecute: sudo $0"
fi

# ─────────────────────────────────────────────────────────────
# 2. Verificar dependencias
# ─────────────────────────────────────────────────────────────
info "Verificando dependencias..."
for pkg in live-build debootstrap xorriso squashfs-tools; do
    if ! command -v "$pkg" &>/dev/null && ! dpkg -s "$pkg" &>/dev/null; then
        info "Instalando $pkg..."
        apt-get update -qq
        apt-get install -y -qq "$pkg" || error "No se pudo instalar $pkg"
    fi
done
ok "Dependencias listas"

# ─────────────────────────────────────────────────────────────
# 3. Preparar directorio de build
# ─────────────────────────────────────────────────────────────
info "Preparando directorio de build en ${BUILD_DIR}..."
if [ -d "$BUILD_DIR" ]; then
    read -p "${BUILD_DIR} ya existe. ¿Eliminarlo y continuar? [s/N]: " resp
    if [[ "$resp" =~ ^[Ss]$ ]]; then
        rm -rf "$BUILD_DIR"
    else
        error "Cancelado por el usuario"
    fi
fi

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# ─────────────────────────────────────────────────────────────
# 4. Configurar live-build
# ─────────────────────────────────────────────────────────────
info "Configurando live-build para Debian ${DEBIAN_DIST} ${ARCH}..."

lb config \
    --distribution "$DEBIAN_DIST" \
    --architecture "$ARCH" \
    --binary-images iso-hybrid \
    --bootloader grub-efi \
    --debian-installer none \
    --archive-areas "main contrib non-free non-free-firmware" \
    --apt-indices false \
    --win32-loader false \
    --iso-application "ForensicSuite Live" \
    --iso-volume "FORENSICSUITE" \
    --image-name forensic-suite-live \
    --updates true \
    --security true \
    --backports false \
    --firmware-binary true \
    --firmware-chroot true \
    --mirror-bootstrap http://deb.debian.org/debian \
    --mirror-chroot http://deb.debian.org/debian \
    --mirror-chroot-security http://security.debian.org/debian-security \
    --mirror-binary http://deb.debian.org/debian \
    --mirror-binary-security http://security.debian.org/debian-security

# ─────────────────────────────────────────────────────────────
# 5. Lista de paquetes forenses del sistema
# ─────────────────────────────────────────────────────────────
info "Generando lista de paquetes..."
cat > config/package-lists/forensic.list.chroot << 'EOF'
# Forense básica disponible en Debian trixie
scalpel
dcfldd
gnupg
openssl
hdparm
util-linux
mtools
sleuthkit
foremost
binwalk
libimage-exiftool-perl
python3
python3-pip
python3-venv
python3-psutil
bash-completion
vim
nano
less
fdisk
gparted
cryptsetup
lvm2
mdadm
smartmontools
linux-headers-amd64
wireshark
tshark
net-tools
iptables
curl
wget
ca-certificates
EOF

# ─────────────────────────────────────────────────────────────
# 6. Incluir ForensicSuite en el Live
# ─────────────────────────────────────────────────────────────
info "Copiando ForensicSuite al entorno Live..."
mkdir -p config/includes.chroot/opt/forensic_suite
rsync -a \
    --exclude='live-build' \
    --exclude='.venv' \
    --exclude='*.iso' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    "$PROJECT_DIR"/ config/includes.chroot/opt/forensic_suite/

# ─────────────────────────────────────────────────────────────
# 7. Hook de instalación en tiempo de build (todo queda en la ISO)
# ─────────────────────────────────────────────────────────────
info "Configurando instalación de herramientas en el chroot..."
mkdir -p config/hooks/normal
cat > config/hooks/normal/9990-forensic-suite-tools.hook.chroot << 'EOF'
#!/bin/bash
set -e

LOG="/var/log/forensic_suite_build.log"
mkdir -p "$(dirname "$LOG")"
echo "[ForensicSuite] Instalando herramientas forenses en la ISO..." | tee "$LOG"

# Actualizar índices e intentar instalar herramientas opcionales de repositorios
apt-get update -qq
for pkg in autopsy bulk-extractor; do
    if apt-cache show "$pkg" >/dev/null 2>&1; then
        echo "[ForensicSuite] Instalando $pkg..." | tee -a "$LOG"
        apt-get install -y --no-install-recommends "$pkg" >>"$LOG" 2>&1 || true
    else
        echo "[ForensicSuite] $pkg no disponible en repositorios, omitiendo" | tee -a "$LOG"
    fi
done

# Preparar virtualenv para herramientas Python
VENV_DIR="/opt/forensic_suite_venv"
python3 -m venv "$VENV_DIR" || {
    echo "[ForensicSuite] ERROR: No se pudo crear virtualenv" | tee -a "$LOG" >&2
    exit 1
}
PIP="$VENV_DIR/bin/pip"
PYTHON="$VENV_DIR/bin/python"
$PIP install --upgrade pip setuptools wheel >>"$LOG" 2>&1

# Volatility3 vía pip (incluido en la ISO)
echo "[ForensicSuite] Instalando volatility3 vía pip..." | tee -a "$LOG"
if $PIP install volatility3 >>"$LOG" 2>&1; then
    ln -sf "$VENV_DIR/bin/vol" /usr/local/bin/vol 2>/dev/null || true
    ln -sf "$VENV_DIR/bin/volatility" /usr/local/bin/volatility 2>/dev/null || true
    echo "[ForensicSuite] volatility3 instalado" | tee -a "$LOG"
else
    echo "[ForensicSuite] No se pudo instalar volatility3 vía pip" | tee -a "$LOG"
fi

# AVML desde GitHub releases (binario estático)
echo "[ForensicSuite] Descargando AVML..." | tee -a "$LOG"
AVML_URL=""
if command -v curl >/dev/null 2>&1; then
    AVML_URL=$(curl -s https://api.github.com/repos/microsoft/avml/releases/latest 2>/dev/null | \
        grep '"browser_download_url"' | grep 'avml' | grep -v 'avml.minimal' | grep -v 'avml-convert' | head -n1 | \
        sed -E 's/.*"([^"]+)".*/\1/')
fi
if [ -z "$AVML_URL" ] && command -v wget >/dev/null 2>&1; then
    AVML_URL=$(wget -qO- https://api.github.com/repos/microsoft/avml/releases/latest 2>/dev/null | \
        grep '"browser_download_url"' | grep 'avml' | grep -v 'avml.minimal' | grep -v 'avml-convert' | head -n1 | \
        sed -E 's/.*"([^"]+)".*/\1/')
fi
if [ -n "$AVML_URL" ]; then
    echo "[ForensicSuite] URL AVML: $AVML_URL" | tee -a "$LOG"
    if curl -L -o /usr/local/bin/avml "$AVML_URL" >>"$LOG" 2>&1 || \
       wget -qO /usr/local/bin/avml "$AVML_URL" >>"$LOG" 2>&1; then
        chmod +x /usr/local/bin/avml
        echo "[ForensicSuite] AVML instalado en /usr/local/bin/avml" | tee -a "$LOG"
    else
        echo "[ForensicSuite] No se pudo descargar AVML" | tee -a "$LOG"
    fi
else
    echo "[ForensicSuite] No se encontró URL de descarga para AVML" | tee -a "$LOG"
fi

# Instalar ForensicSuite desde el directorio incluido en la ISO
PROJECT_DIR="/opt/forensic_suite"
if [ -f "${PROJECT_DIR}/setup.py" ] || [ -f "${PROJECT_DIR}/pyproject.toml" ]; then
    echo "[ForensicSuite] Instalando ForensicSuite en virtualenv..." | tee -a "$LOG"
    if $PIP install "${PROJECT_DIR}[full]" >>"$LOG" 2>&1; then
        echo "[ForensicSuite] Instalación por pip exitosa" | tee -a "$LOG"
    else
        echo "[ForensicSuite] ERROR: No se pudo instalar ForensicSuite" | tee -a "$LOG" >&2
        exit 1
    fi
else
    echo "[ForensicSuite] ERROR: No se encontró setup.py ni pyproject.toml en ${PROJECT_DIR}" | tee -a "$LOG" >&2
    exit 1
fi

# Enlaces de ForensicSuite en /usr/local/bin
ln -sf "$VENV_DIR/bin/forensic_suite" /usr/local/bin/forensic_suite
ln -sf "$VENV_DIR/bin/fs" /usr/local/bin/fs
EOF
chmod +x config/hooks/normal/9990-forensic-suite-tools.hook.chroot

# ─────────────────────────────────────────────────────────────
# 8. Hook post-build: accesos directos en el escritorio del Live
# ─────────────────────────────────────────────────────────────
info "Configurando accesos directos de escritorio..."
cat > config/hooks/normal/9991-forensic-suite-desktop.hook.chroot << 'EOF'
#!/bin/bash
set -e

for userdir in /home/*/; do
    [ -d "$userdir" ] || continue
    username=$(basename "$userdir")
    desktop="${userdir}Desktop"
    mkdir -p "$desktop"
    cat > "${desktop}/forensic-suite.desktop" << 'DESKTOP'
[Desktop Entry]
Name=ForensicSuite Terminal
Comment=Framework de Análisis Forense Digital
Exec=bash -c 'sudo forensic_suite --help; exec bash'
Icon=utilities-terminal
Type=Application
Terminal=true
DESKTOP
    chmod +x "${desktop}/forensic-suite.desktop"
    chown -R "$username:$username" "$desktop" 2>/dev/null || true
done
EOF
chmod +x config/hooks/normal/9991-forensic-suite-desktop.hook.chroot

# ─────────────────────────────────────────────────────────────
# 8. Hook de bienvenida
# ─────────────────────────────────────────────────────────────
mkdir -p config/includes.chroot/etc/skel/
cat > config/includes.chroot/etc/skel/.bashrc << 'EOF'
# ForensicSuite Live - ~/.bashrc
export PATH="/usr/local/bin:$PATH"
export PS1='\[\033[01;31m\]forensic\[\033[00m\]:\w\$ '

cat << 'BANNER'

  ╔═══════════════════════════════════════════════════════════════╗
  ║                                                               ║
  ║   ForensicSuite Live v2.0.0 - Entorno Forense Debian Live    ║
  ║   Uso: forensic_suite --help  |  sudo forensic_suite listar   ║
  ║                                                               ║
  ╚═══════════════════════════════════════════════════════════════╝

BANNER

# Recordatorio de seguridad
alias bloquear='sudo forensic_suite bloquear'
alias desbloquear='sudo forensic_suite desbloquear'
EOF

# ─────────────────────────────────────────────────────────────
# 9. Construir la ISO
# ─────────────────────────────────────────────────────────────
info "Construyendo ISO (esto puede tardar varios minutos)..."
lb build

# ─────────────────────────────────────────────────────────────
# 10. Mover ISO de salida
# ─────────────────────────────────────────────────────────────
ISO_NAME=$(ls -1 live-image-${ARCH}.hybrid.iso 2>/dev/null || ls -1 *.iso | head -n1)
if [ -f "$ISO_NAME" ]; then
    cp "$ISO_NAME" "$ISO_OUTPUT"
    ok "ISO creada: ${ISO_OUTPUT}"
    ls -lh "$ISO_OUTPUT"
else
    error "No se encontró la ISO generada"
fi

info "Para grabar en USB: sudo dd if=${ISO_OUTPUT} of=/dev/sdX bs=4M status=progress"
info "Reemplaza /dev/sdX por tu dispositivo USB. ¡CUIDADO!"
