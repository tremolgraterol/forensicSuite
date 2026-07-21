#!/bin/bash
# =============================================================
# ForensicSuite - Instalador del Sistema
# =============================================================
# Ejecutar como root para instalacion global:
#   sudo ./install.sh
#
# Sin root para instalacion en usuario:
#   ./install.sh --user
# =============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

VERSION="2.0.0"

echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}  ForensicSuite v${VERSION} - Instalador        ${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# ─────────────────────────────────────────────────────────────
# Dependencias del sistema
# ─────────────────────────────────────────────────────────────
instalar_dependencias_sistema() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}No se ejecuta como root. Saltando instalacion de paquetes del sistema.${NC}"
        echo -e "${YELLOW}Instale manualmente:${NC}"
        echo "  sudo apt install hdparm util-linux gnupg openssl scalpel bulk-extractor python3-venv"
        return 0
    fi

    if ! command -v apt-get &>/dev/null; then
        echo -e "${YELLOW}apt-get no encontrado. No se instalaran paquetes del sistema automaticamente.${NC}"
        return 0
    fi

    echo -e "${CYAN}Instalando dependencias del sistema...${NC}"

    # Actualizar listas silenciosamente
    apt-get update -qq

    # Paquetes esenciales forenses
    PAQUETES=(
        "hdparm"
        "util-linux"
        "gnupg"
        "openssl"
        "scalpel"
        "bulk-extractor"
        "python3-venv"
        "python3-pip"
    )

    for pkg in "${PAQUETES[@]}"; do
        if dpkg -s "$pkg" &>/dev/null; then
            echo -e "${GREEN}  [OK]${NC} $pkg"
        else
            echo -e "${CYAN}  [INSTALANDO]${NC} $pkg"
            apt-get install -y -qq "$pkg" || {
                echo -e "${YELLOW}  [AVISO] No se pudo instalar $pkg. Continuando...${NC}"
            }
        fi
    done

    echo -e "${GREEN}Dependencias del sistema procesadas.${NC}"
    echo ""
}

# Instalar dependencias del sistema al inicio (requiere root)
instalar_dependencias_sistema

# Detectar Python
PYTHON=""
for cmd in python3 python3.12 python3.11 python3.10 python3.9; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}Error: Python 3.9+ no encontrado${NC}"
    echo "Instale Python: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${GREEN}Python detectado:${NC} $PYTHON ($PY_VERSION)"

# Verificar version minima
$PYTHON -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: se requiere Python 3.9+, tiene $PY_VERSION${NC}"
    exit 1
fi

# Detectar modo de instalacion
INSTALL_MODE="user"
if [ "$1" = "--system" ] || [ "$1" = "--global" ]; then
    INSTALL_MODE="system"
fi

if [ "$EUID" -eq 0 ] && [ "$1" != "--user" ]; then
    INSTALL_MODE="system"
fi

echo ""
if [ "$INSTALL_MODE" = "system" ]; then
    echo -e "${YELLOW}Modo: INSTALACION GLOBAL (requiere pip del sistema)${NC}"
    echo ""

    # Crear virtualenv para no ensuciar el sistema
    VENV_DIR="/opt/forensic_suite"
    echo -e "${CYAN}Creando virtualenv en $VENV_DIR...${NC}"
    $PYTHON -m venv "$VENV_DIR" 2>/dev/null || {
        echo -e "${YELLOW}python3-venv no disponible, intentando con pip --user...${NC}"
        INSTALL_MODE="user"
    }

    if [ "$INSTALL_MODE" = "system" ]; then
        source "$VENV_DIR/bin/activate"
        pip install --upgrade pip setuptools wheel
        pip install -e "$SCRIPT_DIR"[full]

        # Crear symlink en /usr/local/bin
        ln -sf "$VENV_DIR/bin/forensic_suite" /usr/local/bin/forensic_suite
        ln -sf "$VENV_DIR/bin/fs" /usr/local/bin/fs

        echo -e "${GREEN}Instalado globalmente:${NC}"
        echo "  forensic_suite -> /usr/local/bin/forensic_suite"
        echo "  fs             -> /usr/local/bin/fs (atajo)"
        echo "  Virtualenv:    $VENV_DIR"
    fi
fi

if [ "$INSTALL_MODE" = "user" ]; then
    echo -e "${YELLOW}Modo: INSTALACION USUARIO (--user)${NC}"
    echo ""

    $PYTHON -m pip install --user -e "$SCRIPT_DIR"[full] 2>/dev/null || {
        echo -e "${YELLOW}pip --user falló, creando symlink manual...${NC}"
        BIN_DIR="$HOME/.local/bin"
        mkdir -p "$BIN_DIR"

        cat > "$BIN_DIR/forensic_suite" << WRAPPER
#!/bin/bash
PROJECT_DIR="$SCRIPT_DIR"
PYTHONPATH="\$PROJECT_DIR" python3 -m forensic_suite "\$@"
WRAPPER
        chmod +x "$BIN_DIR/forensic_suite"
        ln -sf "$BIN_DIR/forensic_suite" "$BIN_DIR/fs"

        echo -e "${GREEN}Wrapper creado:${NC} $BIN_DIR/forensic_suite"
    }

    # Verificar que ~/.local/bin esta en PATH
    if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
        echo ""
        echo -e "${YELLOW}~/.local/bin no esta en PATH. Agregando a .bashrc...${NC}"
        echo '' >> "$HOME/.bashrc"
        echo '# ForensicSuite' >> "$HOME/.bashrc"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
        echo -e "${GREEN}Agregado a .bashrc. Ejecute: source ~/.bashrc${NC}"
    fi
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  INSTALACION COMPLETADA                   ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "Comandos disponibles:"
echo -e "  ${CYAN}forensic_suite${NC}          Comando completo"
echo -e "  ${CYAN}fs${NC}                      Atajo rapido"
echo ""
echo -e "Uso rapido:"
echo -e "  forensic_suite --version"
echo -e "  forensic_suite hash archivo.raw"
echo -e "  forensic_suite listar"
echo -e "  forensic_suite perito --configurar"
echo ""
echo -e "Requiere sudo para bloqueo de dispositivos:"
echo -e "  ${CYAN}sudo forensic_suite bloquear /dev/sdX${NC}"
echo ""

# Instalar bash completion
echo -e "${CYAN}Instalando bash completion...${NC}"

COMPLETION_DIR="$HOME/.local/share/bash-completion/completions"
mkdir -p "$COMPLETION_DIR"

# Copiar script de completion
if [ -f "$SCRIPT_DIR/forensic_suite_completion.sh" ]; then
    cp "$SCRIPT_DIR/forensic_suite_completion.sh" "$COMPLETION_DIR/forensic_suite"
    echo -e "${GREEN}Completion instalado en:${NC} $COMPLETION_DIR/forensic_suite"
else
    # Crear completion inline
    cat > "$COMPLETION_DIR/forensic_suite" << 'COMPLETION'
#!/bin/bash
_forensic_suite_completions()
{
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    commands="hash verificar bloquear desbloquear listar acta firmar verificar-firma claves timestamp verificar-timestamp manifest verificar-manifest carve analyze memoria perito daemon interact"

    if [ ${COMP_CWORD} -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi

    if [[ "${cur}" == -* ]]; then
        local cmd="${COMP_WORDS[1]}"
        case "${cmd}" in
            hash)                  COMPREPLY=( $(compgen -W "-a -g --algoritmo --guardar" -- ${cur}) ); return 0 ;;
            verificar)             COMPREPLY=( $(compgen -W "-a --algoritmo" -- ${cur}) ); return 0 ;;
            bloquear|desbloquear)  COMPREPLY=(); return 0 ;;
            listar)                COMPREPLY=( $(compgen -W "-s --incluir-sistema" -- ${cur}) ); return 0 ;;
            acta)                  COMPREPLY=( $(compgen -W "--perito --cedula --cargo --caso -t --transferir --cerrar --autoridad -o --salida --json" -- ${cur}) ); return 0 ;;
            firmar)                COMPREPLY=( $(compgen -W "--key -o --salida" -- ${cur}) ); return 0 ;;
            timestamp)             COMPREPLY=( $(compgen -W "--tsa -a --algoritmo -o --token-salida" -- ${cur}) ); return 0 ;;
            verificar-timestamp)   COMPREPLY=(); return 0 ;;
            manifest)              COMPREPLY=( $(compgen -W "--caso --perito -o --salida -e --extensiones -x --excluir -v --verificar" -- ${cur}) ); return 0 ;;
            verificar-manifest)    COMPREPLY=(); return 0 ;;
            carve)                 COMPREPLY=( $(compgen -W "-o --salida --caso --perito -c --config -p --perfil --perfiles -m --manifest -v --verbose --verificar-instalacion --listar-tipos" -- ${cur}) ); return 0 ;;
            analyze)               COMPREPLY=(); return 0 ;;
            memoria)               COMPREPLY=( $(compgen -W "--verificar-entorno --adquirir --analizar --verificar --dump --plugin --caso --directorio --estado --cadena --cifrar --firmar --informe" -- ${cur}) ); return 0 ;;
            perito)                COMPREPLY=( $(compgen -W "--configurar --ver --info" -- ${cur}) ); return 0 ;;
            daemon)                COMPREPLY=( $(compgen -W "status install uninstall" -- ${cur}) ); return 0 ;;
            interact)              COMPREPLY=( $(compgen -W "--caso --perito --directorio" -- ${cur}) ); return 0 ;;
        esac
        
        case "${prev}" in
            -a|--algoritmo) COMPREPLY=( $(compgen -W "sha256 sha512 md5" -- ${cur}) ); return 0 ;;
            -p|--perfil)    COMPREPLY=( $(compgen -W "recuperacion medios documentos redes cripto general" -- ${cur}) ); return 0 ;;
        esac
    fi
    
    local cmd="${COMP_WORDS[1]}"
    case "${cmd}" in
        hash|verificar|acta|firmar|timestamp|carve)
            COMPREPLY=( $(compgen -f -- ${cur}) )
            return 0
            ;;
        bloquear|desbloquear)
            COMPREPLY=( $(compgen -G "/dev/sd*" -- ${cur}) $(compgen -G "/dev/nvme*" -- ${cur}) )
            return 0
            ;;
    esac
    
    COMPREPLY=( $(compgen -f -- ${cur}) )
    return 0
}

complete -F _forensic_suite_completions forensic_suite
complete -F _forensic_suite_completions fs
COMPLETION
    echo -e "${GREEN}Completion creado:${NC} $COMPLETION_DIR/forensic_suite"
fi

# Agregar source a .bashrc si no existe
if ! grep -q "bash-completion/completions/forensic_suite" "$HOME/.bashrc" 2>/dev/null; then
    echo "" >> "$HOME/.bashrc"
    echo "# ForensicSuite bash completion" >> "$HOME/.bashrc"
    echo "source ~/.local/share/bash-completion/completions/forensic_suite" >> "$HOME/.bashrc"
    echo -e "${GREEN}Agregado a .bashrc${NC}"
fi

echo ""
echo -e "${YELLOW}Para activar completion ahora:${NC}"
echo -e "  source ~/.bashrc"
echo ""
echo -e "${YELLOW}Prueba:${NC}"
echo -e "  forensic_suite <TAB><TAB>"
echo -e "  forensic_suite hash <TAB><TAB>"
echo -e "  forensic_suite carve -p <TAB><TAB>"
echo ""

echo -e "${YELLOW}AVISO DE SEGURIDAD - Daemon de bloqueo:${NC}"
echo "  El daemon instala una regla udev que bloquea NUEVOS discos conectados"
echo "  despues del arranque, EXCLUYENDO automaticamente el disco raiz."
echo "  Para desinstalar y recuperar el sistema:"
echo "      sudo forensic_suite daemon uninstall"
echo "  El bloqueo es LOGICO POR SOFTWARE; para evidencia judicial formal"
echo "  use un write blocker de HARDWARE certificado."
echo ""
