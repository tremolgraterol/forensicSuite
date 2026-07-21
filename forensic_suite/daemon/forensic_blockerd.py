#!/usr/bin/env python3
"""
forensic_blockerd - Daemon de Bloqueo Forense Automático
======================================================

Demonio que actúa ANTES del auto-mount del sistema operativo,
aplicando bloqueo de escritura (hdparm + blockdev) en el momento
exacto en que el kernel detecta un nuevo dispositivo de almacenamiento.

Filosofía: "No confiar en el SO, sino obligarlo a actuar bajo
protocolo de nula interacción de escritura."

Modos de operación:
    1. DAEMON (systemd): Se instala como servicio, escucha eventos udev
    2. MANUAL: Ejecución puntual, bloquea dispositivos existentes
    3. UDEV RULE: Regla udev que ejecuta blockdev --setro inmediatamente

El script auto-detecta el entorno y decide el modo óptimo.

Autor: Tr3w01
Versión: 2.0.0
Protocolos: ISO 27037 / NIST SP 800-86 / RFC 3227
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────
# constantes
# ─────────────────────────────────────────────────────────────

VERSION = "2.0.0"
CONFIG_DIR = Path("/etc/forensic_suite")
CONFIG_FILE = CONFIG_DIR / "forensic-block.conf"
LOG_DIR = Path("/var/log/forensic_suite")
LOG_FILE = LOG_DIR / "blockerd.log"
UDEV_RULE = Path("/etc/udev/rules.d/10-forensic-block.rules")
UDEV_RULE_SOURCE = Path(__file__).parent / "10-forensic-block.rules"
SERVICE_FILE = Path("/etc/systemd/system/forensic-blockerd.service")
SERVICE_SOURCE = Path(__file__).parent / "forensic-blockerd.service"

# Rutas de herramientas (sbin no está en PATH de usuario)
sbin_paths = ["/usr/sbin", "/sbin"]
for p in sbin_paths:
    if p not in os.environ.get("PATH", ""):
        os.environ["PATH"] = p + ":" + os.environ.get("PATH", "")

HDPARM = "hdparm"
BLOCKDEV = "blockdev"
LOSETUP = "losetup"
LSBLK = "lsblk"

# Dispositivos excluidos por defecto (no bloquear el disco raíz)
DISPOSITIVOS_EXCLUIDOS_DEFAULT = []

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S"
)
logger = logging.getLogger("forensic_blockerd")


# ─────────────────────────────────────────────────────────────
# utilidades del sistema
# ─────────────────────────────────────────────────────────────

def ejecutar(comando: list, sudo: bool = False, timeout: int = 10) -> dict:
    """Ejecuta un comando del sistema."""
    if sudo:
        comando = ["sudo"] + comando
    try:
        r = subprocess.run(
            comando, capture_output=True, text=True, timeout=timeout
        )
        return {"ok": r.returncode == 0, "stdout": r.stdout.strip(),
                "stderr": r.stderr.strip(), "code": r.returncode}
    except FileNotFoundError:
        return {"ok": False, "stdout": "", "stderr": f"No encontrado: {comando[0]}", "code": -1}
    except subprocess.TimeoutExpired:
        return {"ok": False, "stdout": "", "stderr": "Timeout", "code": -2}


def es_root() -> bool:
    return os.geteuid() == 0


def _dispositivo_es_removible(ruta: str) -> bool:
    """Determina si un dispositivo de bloque es removible (USB, SD)."""
    nombre = Path(ruta).name
    sys_path = Path(f"/sys/block/{nombre}/removable")
    if sys_path.exists():
        try:
            return sys_path.read_text().strip() == "1"
        except Exception:
            pass
    r = ejecutar(["lsblk", "-no", "RM", ruta])
    if r["ok"] and r["stdout"]:
        return r["stdout"].strip().split("\n")[0] == "1"
    return False


def _punto_montaje_a_dispositivo(punto: str) -> Optional[str]:
    """Obtiene el dispositivo de bloque padre asociado a un punto de montaje."""
    r = ejecutar(["findmnt", "-n", "-o", "SOURCE", punto])
    if not (r["ok"] and r["stdout"]):
        return None

    source = r["stdout"].strip()
    if not source.startswith("/dev/"):
        return None

    r2 = ejecutar(["lsblk", "-no", "PKNAME", source])
    if r2["ok"] and r2["stdout"]:
        pkname = r2["stdout"].strip().split("\n")[0]
        if pkname:
            return f"/dev/{pkname}"

    base = source[5:].rstrip("0123456789")
    if base.endswith("p") and len(base) > 1 and base[-2].isdigit():
        base = base[:-1]
    return f"/dev/{base}" if base else source


def _es_entorno_live() -> bool:
    """Detecta si el sistema corre desde un medio Live/USB."""
    puntos_live = [
        "/run/live/medium",
        "/lib/live/mount/medium",
        "/cdrom",
        "/run/initramfs/live",
    ]
    for punto in puntos_live:
        if Path(punto).is_mount():
            return True

    r = ejecutar(["findmnt", "-n", "-o", "FSTYPE", "/"])
    if r["ok"] and r["stdout"]:
        fstype = r["stdout"].strip().lower()
        if fstype in ("overlay", "overlayfs", "aufs", "squashfs", "tmpfs"):
            return True

    try:
        cmdline = Path("/proc/cmdline").read_text().lower()
        if any(x in cmdline for x in ("boot=live", "boot=casper", "live-media", "liveimg")):
            return True
    except Exception:
        pass

    return False


def dispositivo_raiz() -> str:
    """
    Retorna el dispositivo raíz del sistema operativo.

    En entornos Live/USB identifica el dispositivo Live como raíz,
    permitiendo que la regla udev bloquee discos internos del anfitrión.
    Usa findmnt y blkid para soportar particiones, LVM, LUKS y NVMe.
    """
    # Estrategia 0: entorno Live/USB
    if _es_entorno_live():
        for punto in ["/run/live/medium", "/lib/live/mount/medium", "/cdrom", "/run/initramfs/live"]:
            dev = _punto_montaje_a_dispositivo(punto)
            if dev:
                return dev

        r = ejecutar(["findmnt", "-n", "-o", "SOURCE", "/run"])
        if r["ok"] and r["stdout"]:
            source = r["stdout"].strip()
            if source.startswith("/dev/"):
                dev_padre = _punto_montaje_a_dispositivo("/run")
                if dev_padre and _dispositivo_es_removible(dev_padre):
                    return dev_padre

    # Estrategia 1: source real de /
    r = ejecutar(["findmnt", "-n", "-o", "SOURCE", "/"])
    if r["ok"] and r["stdout"]:
        source = r["stdout"].strip()
        if source.startswith("/dev/"):
            r2 = ejecutar(["lsblk", "-no", "PKNAME", source])
            if r2["ok"] and r2["stdout"]:
                pkname = r2["stdout"].strip().split("\n")[0]
                if pkname:
                    return f"/dev/{pkname}"
            base = source[5:].rstrip("0123456789")
            if base.endswith("p") and len(base) > 1 and base[-2].isdigit():
                base = base[:-1]
            if base:
                return f"/dev/{base}"
            return source

    # Estrategia 2: UUID del sistema de archivos raíz
    r = ejecutar(["findmnt", "-n", "-o", "UUID", "/"])
    if r["ok"] and r["stdout"]:
        uuid = r["stdout"].strip()
        r2 = ejecutar(["blkid", "-U", uuid])
        if r2["ok"] and r2["stdout"]:
            dev = r2["stdout"].strip()
            r3 = ejecutar(["lsblk", "-no", "PKNAME", dev])
            if r3["ok"] and r3["stdout"]:
                pkname = r3["stdout"].strip().split("\n")[0]
                if pkname:
                    return f"/dev/{pkname}"
            return dev

    # Fallback de último recurso
    return "/dev/sda"


# ─────────────────────────────────────────────────────────────
# config
# ─────────────────────────────────────────────────────────────

def cargar_config() -> dict:
    """Carga configuración del daemon."""
    config = {
        "excluir_raiz": True,
        "excluir_dispositivos": [],
        "hdparm": True,
        "blockdev": True,
        "log_level": "INFO",
        "auto_instalar_udev": True
    }
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE) as f:
                config.update(json.load(f))
        except Exception:
            pass
    return config


def guardar_config(config: dict):
    """Guarda configuración."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2, sort_keys=True)


# ─────────────────────────────────────────────────────────────
# operaciones de bloqueo
# ─────────────────────────────────────────────────────────────

def bloquear_dispositivo(ruta: str) -> dict:
    """
    Aplica bloqueo de escritura a un dispositivo.

    Ejecuta en orden:
        1. blockdev --setro (kernel block layer)
        2. hdparm -r1 (firmware)

    Retorna dict con estado de cada operación.
    """
    nombre = Path(ruta).name
    resultado = {
        "dispositivo": ruta,
        "timestamp": datetime.now().isoformat(),
        "blockdev": False,
        "hdparm": False,
        "verificado": False,
        "error": None
    }

    # CAPA 1: Kernel block layer
    r = ejecutar([BLOCKDEV, "--setro", ruta], sudo=True)
    resultado["blockdev"] = r["ok"]
    if not r["ok"]:
        resultado["error"] = f"blockdev --setro falló: {r['stderr']}"
        logger.error(f"[BLOQUEO FALLIDO] {ruta}: blockdev - {r['stderr']}")
        return resultado

    # CAPA 2: Firmware
    r = ejecutar([HDPARM, "-r1", ruta], sudo=True)
    resultado["hdparm"] = r["ok"]
    if not r["ok"]:
        logger.warning(f"[WARN] {ruta}: hdparm -r1 falló (no crítico): {r['stderr']}")

    # Verificación
    r = ejecutar([BLOCKDEV, "--getro", ruta], sudo=True)
    resultado["verificado"] = r["ok"] and r["stdout"] == "1"

    if resultado["verificado"]:
        logger.info(f"[BLOQUEADO] {ruta} - blockdev=OK hdparm={'OK' if resultado['hdparm'] else 'WARN'}")
    else:
        resultado["error"] = f"Verificación fallida: getro={r['stdout']}"
        logger.error(f"[VERIFICACIÓN FALLIDA] {ruta}: getro={r['stdout']}")

    return resultado


def desbloquear_dispositivo(ruta: str) -> dict:
    """Restaura escritura en un dispositivo."""
    resultado = {"dispositivo": ruta, "blockdev": False, "hdparm": False}

    r = ejecutar([BLOCKDEV, "--setrw", ruta], sudo=True)
    resultado["blockdev"] = r["ok"]

    r = ejecutar([HDPARM, "-r0", ruta], sudo=True)
    resultado["hdparm"] = r["ok"]

    logger.info(f"[DESBLOQUEADO] {ruta}")
    return resultado


def listar_dispositivos_bloqueables(excluir_root: bool = True) -> list:
    """Lista dispositivos que deben ser bloqueados."""
    r = ejecutar([LSBLK, "-J", "-o", "NAME,TYPE,SIZE,MODEL,SERIAL"])
    if not r["ok"]:
        return []

    try:
        datos = json.loads(r["stdout"])
    except json.JSONDecodeError:
        return []

    raiz = dispositivo_raiz() if excluir_root else ""
    dispositivos = []

    for dev in datos.get("blockdevices", []):
        if dev.get("type") != "disk":
            continue
        nombre = dev.get("name", "")
        ruta = f"/dev/{nombre}"

        if excluir_root and ruta == raiz:
            continue
        if nombre.startswith("loop") or nombre.startswith("ram"):
            continue

        dispositivos.append({
            "ruta": ruta,
            "modelo": dev.get("model", "unknown") or "unknown",
            "serial": dev.get("serial", "unknown") or "unknown",
            "tamano": dev.get("size", "unknown")
        })

    return dispositivos


# ─────────────────────────────────────────────────────────────
# MODO 1: DAEMON (escucha eventos udev)
# ─────────────────────────────────────────────────────────────

class ForensicBlockerd:
    """
    Daemon que escucha eventos udev y bloquea dispositivos
    ANTES de que udisks2 pueda montarlos.
    """

    def __init__(self, config: dict):
        self.config = config
        self._running = True
        self._stats = {
            "dispositivos_bloqueados": 0,
            "intentos_fallidos": 0,
            "inicio": datetime.now().isoformat()
        }

    def _signal_handler(self, signum, frame):
        logger.info(f"[SEÑAL {signum}] Deteniendo daemon...")
        self._running = False

    def iniciar(self):
        """Inicia el daemon."""
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info("=" * 60)
        logger.info(f"forensic_blockerd v{VERSION} - Daemon de Bloqueo Forense")
        logger.info("=" * 60)
        logger.info(f"PID: {os.getpid()}")
        logger.info(f"Config: {self.config}")
        logger.info(f"Dispositivo raíz (excluido): {dispositivo_raiz()}")
        logger.info("Escuchando eventos de dispositivos...")

        # Bloquear dispositivos existentes al iniciar
        self._bloquear_existentes()

        # Loop principal: escuchar eventos udev
        self._escuchar_udev()

    def _bloquear_existentes(self):
        """Bloquea todos los dispositivos conectados al iniciar."""
        dispositivos = listar_dispositivos_bloqueables(
            excluir_root=self.config.get("excluir_raiz", True)
        )
        for dev in dispositivos:
            if dev["ruta"] not in self.config.get("excluir_dispositivos", []):
                r = bloquear_dispositivo(dev["ruta"])
                if r["verificado"]:
                    self._stats["dispositivos_bloqueados"] += 1

    def _escuchar_udev(self):
        """
        Escucha eventos udev netlink para dispositivos block.
        Se ejecuta como daemon de fondo (systemd).
        """
        try:
            import pyudev
            context = pyudev.Context()
            monitor = pyudev.Monitor.from_netlink(context)
            monitor.filter_by(subsystem="block", device_type="disk")

            logger.info("Monitor udev activo. Esperando dispositivos...")

            for device in monitor:
                if not self._running:
                    break

                accion = device.action
                ruta = device.device_node

                if accion == "add" and ruta:
                    logger.info(f"[EVENTO UDEV] add: {ruta} ({device.get('ID_MODEL', 'unknown')})")

                    # Verificar que no esté excluido
                    if ruta in self.config.get("excluir_dispositivos", []):
                        logger.info(f"[EXCLUIDO] {ruta} está en lista de exclusión")
                        continue

                    # Bloquear INMEDIATAMENTE
                    r = bloquear_dispositivo(ruta)
                    if r["verificado"]:
                        self._stats["dispositivos_bloqueados"] += 1
                    else:
                        self._stats["intentos_fallidos"] += 1
                        logger.critical(f"[CRÍTICO] Bloqueo fallido en {ruta}: {r['error']}")

                elif accion == "remove" and ruta:
                    logger.info(f"[EVENTO UDEV] remove: {ruta}")

        except ImportError:
            logger.warning("pyudev no instalado. Usando polling como fallback...")
            self._polling_loop()

    def _polling_loop(self):
        """
        Fallback: polling periódico para detectar nuevos dispositivos.
        Se usa si pyudev no está disponible.
        """
        dispositivos_conocidos = set()

        # Cargar dispositivos existentes
        for dev in listar_dispositivos_bloqueables(
            excluir_root=self.config.get("excluir_raiz", True)
        ):
            dispositivos_conocidos.add(dev["ruta"])

        logger.info(f"[POLLING] Monitoreando {len(dispositivos_conocidos)} dispositivos conocidos")

        while self._running:
            time.sleep(2)

            dispositivos_actuales = set()
            for dev in listar_dispositivos_bloqueables(
                excluir_root=self.config.get("excluir_raiz", True)
            ):
                dispositivos_actuales.add(dev["ruta"])

            # Detectar nuevos dispositivos
            nuevos = dispositivos_actuales - dispositivos_conocidos
            for ruta in nuevos:
                if ruta not in self.config.get("excluir_dispositivos", []):
                    logger.info(f"[NUEVO DISPOSITIVO] {ruta}")
                    r = bloquear_dispositivo(ruta)
                    if r["verificado"]:
                        self._stats["dispositivos_bloqueados"] += 1
                    else:
                        self._stats["intentos_fallidos"] += 1

            # Detectar dispositivos removidos
            removidos = dispositivos_conocidos - dispositivos_actuales
            for ruta in removidos:
                logger.info(f"[DISPOSITIVO REMOVIDO] {ruta}")

            dispositivos_conocidos = dispositivos_actuales

    def estado(self) -> dict:
        """Retorna estado actual del daemon."""
        return {
            "version": VERSION,
            "pid": os.getpid(),
            "running": self._running,
            "stats": self._stats,
            "config": self.config
        }


# ─────────────────────────────────────────────────────────────
# MODO 2: UDEV RULE (regla que se ejecuta antes de todo)
# ─────────────────────────────────────────────────────────────

def instalar_regla_udev() -> dict:
    """
    Instala la regla udev que bloquea nuevos dispositivos de almacenamiento
    EXCLUYENDO SIEMPRE el disco raíz del sistema operativo.

    La regla se ejecuta de forma síncrona en el kernel cuando se conecta
    un nuevo dispositivo, pero NUNCA se aplica a dispositivos existentes
    para evitar bloquear el disco de arranque.
    """
    if not es_root():
        return {"ok": False, "error": "Se requiere root para instalar regla udev"}

    raiz = dispositivo_raiz()
    logger.info(f"[UDEV] Disco raíz detectado: {raiz}. Será excluido de la regla.")

    # Generar siempre la regla dinámicamente para incluir el disco raíz actual.
    # No se usa el archivo estático para evitar exclusiones obsoletas.
    contenido = generar_regla_udev(raiz)

    UDEV_RULE.write_text(contenido)
    os.chmod(UDEV_RULE, 0o644)

    # Recargar reglas udev
    r = ejecutar(["udevadm", "control", "--reload-rules"], sudo=True)
    if not r["ok"]:
        return {"ok": False, "error": f"Error recargando udev: {r['stderr']}"}

    # NO ejecutar trigger sobre dispositivos existentes: podría bloquear el disco raíz
    # si la detección falló. Los dispositivos ya conectados deben bloquearse manualmente
    # o reiniciando el sistema con la regla activa.
    logger.warning("[UDEV] No se aplicará la regla a dispositivos ya conectados. "
                 "Reinicie el sistema o use modo manual para bloquear discos existentes.")

    logger.info(f"[UDEV] Regla instalada: {UDEV_RULE}")
    return {"ok": True, "archivo": str(UDEV_RULE), "raiz_excluida": raiz}


def generar_regla_udev(raiz: str = "") -> str:
    """Genera el contenido de la regla udev forense con exclusión del disco raíz."""
    if not raiz:
        raiz = dispositivo_raiz()

    return f"""# ForensicSuite - Bloqueo Automático de Escritura
# ================================================
# Esta regla se ejecuta ANTES de udisks2 (80-udisks2.rules)
# al detectar un NUEVO dispositivo de almacenamiento conectado.
#
# IMPORTANTE: Esta regla NO ES un write blocker de hardware.
# Solo impide escrituras accidentales a nivel kernel. Para evidencia
# judicial debe usarse un bloqueador de escritura físico certificado.
#
# Instalado por: forensic_blockerd v{VERSION}
# Fecha: {datetime.now().isoformat()}
# Protocolo: ISO 27037 / NIST SP 800-86
# Disco raíz excluido: {raiz}

# Solo bloquea discos completos nuevos (no particiones), excluyendo el raíz.
# El bloqueo de particiones debe hacerse manualmente o mediante el daemon.
ACTION=="add", SUBSYSTEM=="block", ENV{{DEVTYPE}}=="disk", KERNEL=="sd*|hd*", ENV{{DEVNAME}}!="{raiz}", \\
  RUN+="/usr/sbin/blockdev --setro %E{{DEVNAME}}"

ACTION=="add", SUBSYSTEM=="block", ENV{{DEVTYPE}}=="disk", KERNEL=="nvme[0-9]*n[0-9]*", ENV{{DEVNAME}}!="{raiz}", \\
  RUN+="/usr/sbin/blockdev --setro %E{{DEVNAME}}"

# NOTA: hdparm -r1 NO se aplica automáticamente porque falla en USB/SSD/NVMe.
# Use el modo manual si requiere pruebas de bloqueo adicionales.
"""


# ─────────────────────────────────────────────────────────────
# MODO 3: INSTALACIÓN COMPLETA (daemon + udev + systemd)
# ─────────────────────────────────────────────────────────────

def instalar_daemon() -> dict:
    """
    Instala el daemon completo:
        1. Regla udev (bloqueo inmediato)
        2. Servicio systemd (daemon de monitoreo)
        3. Configuración
    """
    resultados = {}

    # 1. Instalar regla udev
    resultados["udev"] = instalar_regla_udev()

    # 2. Instalar servicio systemd
    if SERVICE_SOURCE.exists():
        contenido = SERVICE_SOURCE.read_text()
    else:
        contenido = generar_service_systemd()

    if es_root():
        SERVICE_FILE.write_text(contenido)
        os.chmod(SERVICE_FILE, 0o644)
        ejecutar(["systemctl", "daemon-reload"], sudo=True)
        resultados["systemd"] = {"ok": True, "archivo": str(SERVICE_FILE)}
    else:
        resultados["systemd"] = {"ok": False, "error": "Se requiere root"}

    # 3. Guardar configuración
    config = cargar_config()
    guardar_config(config)
    resultados["config"] = {"ok": True, "archivo": str(CONFIG_FILE)}

    return resultados


def generar_service_systemd() -> str:
    """Genera el archivo .service de systemd."""
    python_path = sys.executable
    script_path = str(Path(__file__).resolve())

    return f"""[Unit]
Description=ForensicSuite - Daemon de Bloqueo Forense
Documentation=man:hdparm(8),man:blockdev(8)
After=systemd-udev-settle.service
Before=udisks2.service
Requires=systemd-udev-settle.service

[Service]
Type=simple
ExecStartPre=/usr/bin/sync
ExecStart={python_path} {script_path} --daemon
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

# Seguridad
ProtectSystem=strict
ReadWritePaths=/var/log/forensic_suite /etc/forensic_suite
NoNewPrivileges=no
CapabilityBoundingSet=CAP_SYS_ADMIN CAP_SYS_RAWIO

[Install]
WantedBy=multi-user.target
"""


def desbloquear_todos_dispositivos() -> dict:
    """
    Restaura todos los dispositivos de bloque a lectura/escritura.
    Útil para recuperación de emergencia si el sistema quedó bloqueado.
    """
    resultados = {}
    raiz = dispositivo_raiz()
    logger.info(f"[RECUPERACIÓN] Restaurando dispositivos a RW (raíz detectado: {raiz})")

    r = ejecutar([LSBLK, "-J", "-o", "NAME,TYPE"])
    if not r["ok"]:
        return {"ok": False, "error": "No se pudo listar dispositivos"}

    try:
        datos = json.loads(r["stdout"])
    except json.JSONDecodeError:
        return {"ok": False, "error": "Salida de lsblk no es JSON"}

    for dev in datos.get("blockdevices", []):
        nombre = dev.get("name", "")
        tipo = dev.get("type", "")
        ruta = f"/dev/{nombre}"

        # Solo discos y particiones, no loops/ram
        if tipo not in ("disk", "part"):
            continue
        if nombre.startswith(("loop", "ram")):
            continue

        res = desbloquear_dispositivo(ruta)
        resultados[ruta] = res
        if res["blockdev"]:
            logger.info(f"[RECUPERACIÓN] {ruta} restaurado a RW")
        else:
            logger.warning(f"[RECUPERACIÓN] No se pudo restaurar {ruta}")

    return {"ok": True, "dispositivos": resultados}


def desinstalar_daemon() -> dict:
    """Desinstala el daemon y restaura el sistema."""
    resultados = {}

    # Detener servicio
    r = ejecutar(["systemctl", "stop", "forensic-blockerd"], sudo=True)
    resultados["stop"] = r["ok"]

    # Deshabilitar
    r = ejecutar(["systemctl", "disable", "forensic-blockerd"], sudo=True)
    resultados["disable"] = r["ok"]

    # Eliminar servicio
    if SERVICE_FILE.exists():
        SERVICE_FILE.unlink()
        ejecutar(["systemctl", "daemon-reload"], sudo=True)
        resultados["service"] = {"ok": True, "eliminado": True}

    # Eliminar regla udev
    if UDEV_RULE.exists():
        UDEV_RULE.unlink()
        ejecutar(["udevadm", "control", "--reload-rules"], sudo=True)
        resultados["udev"] = {"ok": True, "eliminado": True}

    # Restaurar dispositivos existentes a lectura/escritura
    resultados["recuperacion"] = desbloquear_todos_dispositivos()

    logger.info("[DESINSTALADO] Daemon forense removido")
    return resultados


# ─────────────────────────────────────────────────────────────
# AUTO-DETECCIÓN: Daemon vs Manual
# ─────────────────────────────────────────────────────────────

def detectar_modo() -> str:
    """
    Auto-detecta el modo de operación óptimo.

    Returns:
        "daemon"  - Si systemd + root están disponibles
        "udev"    - Si udev + root están disponibles
        "manual"  - Si no hay privilegios o systemd
    """
    tiene_systemd = Path("/run/systemd/system").exists()
    tiene_root = es_root()
    tiene_udev = Path("/etc/udev/rules.d").exists()

    if tiene_root and tiene_systemd:
        return "daemon"
    elif tiene_root and tiene_udev:
        return "udev"
    else:
        return "manual"


def ejecutar_modo(modo: str, args=None):
    """Ejecuta en el modo detectado."""
    config = cargar_config()

    if modo == "daemon":
        logger.info("[MODO] Daemon (systemd + udev)")
        daemon = ForensicBlockerd(config)
        daemon.iniciar()

    elif modo == "udev":
        logger.info("[MODO] Solo regla udev (sin daemon)")
        r = instalar_regla_udev()
        if r["ok"]:
            logger.info(f"Regla udev instalada: {r['archivo']}")
            logger.info("Los dispositivos serán bloqueados automáticamente al conectar")
        else:
            logger.error(f"Error: {r['error']}")

    elif modo == "manual":
        logger.info("[MODO] Manual (sin daemon ni udev)")
        dispositivos = listar_dispositivos_bloqueables(
            excluir_root=config.get("excluir_raiz", True)
        )

        if not dispositivos:
            logger.info("No hay dispositivos para bloquear")
            return

        logger.info(f"Encontrados {len(dispositivos)} dispositivos:")
        for dev in dispositivos:
            logger.info(f"  - {dev['ruta']}: {dev['modelo']} ({dev['tamano']})")

        for dev in dispositivos:
            r = bloquear_dispositivo(dev["ruta"])
            if r["verificado"]:
                logger.info(f"  ✓ {dev['ruta']} bloqueado exitosamente")
            else:
                logger.error(f"  ✗ {dev['ruta']} FALLO: {r['error']}")


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ForensicSuite - Daemon de Bloqueo Forense",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modos de operación:
  --daemon       Inicia como daemon systemd (escucha eventos udev)
  --install      Instala daemon + regla udev + servicio systemd
  --uninstall    Desinstala todo y restaura el sistema
  --udev         Solo instala la regla udev
  --manual       Bloquea dispositivos existentes una vez
  --status       Muestra estado de los dispositivos
  --list         Lista dispositivos detectados
  --auto         Auto-detecta modo y ejecuta (default)

Ejempros:
  sudo forensic_blockerd --install    # Instalar todo
  sudo forensic_blockerd --daemon     # Ejecutar como daemon
  forensic_blockerd --manual          # Modo manual (sin root para listar)
  sudo forensic_blockerd --uninstall  # Desinstalar
        """
    )

    parser.add_argument("--version", action="version", version=f"forensic_blockerd v{VERSION}")
    parser.add_argument("--daemon", action="store_true", help="Ejecutar como daemon")
    parser.add_argument("--install", action="store_true", help="Instalar daemon completo")
    parser.add_argument("--uninstall", action="store_true", help="Desinstalar daemon")
    parser.add_argument("--udev", action="store_true", help="Solo instalar regla udev")
    parser.add_argument("--manual", action="store_true", help="Modo manual")
    parser.add_argument("--status", action="store_true", help="Estado de dispositivos")
    parser.add_argument("--list", action="store_true", help="Listar dispositivos")
    parser.add_argument("--auto", action="store_true", help="Auto-detectar modo")
    parser.add_argument("--block", type=str, help="Bloquear dispositivo específico")
    parser.add_argument("--unblock", type=str, help="Desbloquear dispositivo específico")

    args = parser.parse_args()

    # Configurar logging a archivo
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if args.version:
        return

    if args.install:
        r = instalar_daemon()
        print(json.dumps(r, indent=2))
        return

    if args.uninstall:
        r = desinstalar_daemon()
        print(json.dumps(r, indent=2))
        return

    if args.udev:
        r = instalar_regla_udev()
        print(json.dumps(r, indent=2))
        return

    if args.block:
        r = bloquear_dispositivo(args.block)
        print(json.dumps(r, indent=2))
        return

    if args.unblock:
        r = desbloquear_dispositivo(args.unblock)
        print(json.dumps(r, indent=2))
        return

    if args.list:
        devs = listar_dispositivos_bloqueables(excluir_root=True)
        print(json.dumps(devs, indent=2))
        return

    if args.status:
        config = cargar_config()
        daemon = ForensicBlockerd(config)
        print(json.dumps(daemon.estado(), indent=2))
        return

    if args.daemon:
        ejecutar_modo("daemon")
        return

    if args.manual:
        ejecutar_modo("manual")
        return

    if args.auto or len(sys.argv) == 1:
        modo = detectar_modo()
        print(f"Modo detectado: {modo}")
        print(f"  systemd: {Path('/run/systemd/system').exists()}")
        print(f"  root: {es_root()}")
        print(f"  udev: {Path('/etc/udev/rules.d').exists()}")
        print()

        if args.auto:
            ejecutar_modo(modo)
        else:
            print("Usa --auto para ejecutar en modo automático")
            print("Usa --install para instalar el daemon")
            print("Usa --manual para modo manual")


if __name__ == "__main__":
    main()
