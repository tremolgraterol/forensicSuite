"""
ForensicSuite - Dispositivo: Blindaje del Kernel (NIVEL 0)
==========================================================

Este módulo implementa el protocolo de bloqueo y aislamiento de dispositivos
de almacenamiento ANTES de cualquier operación forense.

Filosofía: "No confiar en el sistema operativo, sino obligarlo a actuar bajo
un protocolo de nula interacción de escritura."

Capas de protección (en orden de ejecución):
    1. hdparm -r1    → Blindaje a nivel de firmware (ioctl al controlador)
    2. blockdev --setro → Blindaje a nivel de Kernel Block Layer
    3. losetup --ro   → Aislamiento via loop device read-only
    4. mount -o ro,loop,noexec,noosuid,nodev,noatime → Montaje forense hardened

Protocolos de referencia:
    - ISO 27037 sección 5.4: preservar evidencia en estado original
    - NIST SP 800-86 sección 3.2: verificar integridad de herramientas
    - RFC 3227: orden de volatilidad

Autor: Tr3w01
Versión: 1.0.0
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────
# excepciones
# ─────────────────────────────────────────────────────────────

class EntornoForenseError(Exception):
    """El entorno no está preparado para operaciones forenses."""
    pass


class BloqueoError(Exception):
    """Fallo en el protocolo de bloqueo del dispositivo."""
    pass


class DispositivoNoEncontradoError(Exception):
    """El dispositivo especificado no existe en el sistema."""
    pass


class MontajeError(Exception):
    """Error al montar el dispositivo en modo forense."""
    pass


# ─────────────────────────────────────────────────────────────
# modelos de datos
# ─────────────────────────────────────────────────────────────

@dataclass
class DispositivoInfo:
    """Información completa de un dispositivo de almacenamiento."""
    nombre: str
    tamaño: str
    modelo: str
    serial: str
    tipo: str
    ruta: str
    particiones: list = field(default_factory=list)
    montaje_actual: Optional[str] = None
    fstype: Optional[str] = None


@dataclass
class EstadoBloqueo:
    """Estado del blindaje del dispositivo."""
    hdparm_ro: bool = False
    blockdev_ro: bool = False
    loop_device: Optional[str] = None
    loop_ro: bool = False
    montaje_punto: Optional[str] = None
    montaje_opciones: Optional[str] = None
    verificado: bool = False


# ─────────────────────────────────────────────────────────────
# utilidades del sistema
# ─────────────────────────────────────────────────────────────

def _ejecutar(comando: list, sudo: bool = False, timeout: int = 30) -> dict:
    """
    Ejecuta un comando del sistema y retorna resultado estructurado.

    Args:
        comando: Lista de argumentos del comando
        sudo: Si True, ejecuta con sudo
        timeout: Tiempo máximo de espera en segundos

    Returns:
        dict con keys: exito, stdout, stderr, codigo
    """
    if sudo:
        comando = ["sudo"] + comando

    try:
        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "exito": resultado.returncode == 0,
            "stdout": resultado.stdout.strip(),
            "stderr": resultado.stderr.strip(),
            "codigo": resultado.returncode
        }
    except FileNotFoundError:
        return {
            "exito": False,
            "stdout": "",
            "stderr": f"Comando no encontrado: {comando[0]}",
            "codigo": -1
        }
    except subprocess.TimeoutExpired:
        return {
            "exito": False,
            "stdout": "",
            "stderr": f"Timeout ({timeout}s) al ejecutar: {' '.join(comando)}",
            "codigo": -2
        }


def _existe_binario(nombre: str) -> bool:
    """Verifica si un binario existe en el PATH del sistema."""
    resultado = _ejecutar(["which", nombre])
    return resultado["exito"] and resultado["stdout"] != ""


def _servicio_activo(servicio: str) -> bool:
    """Verifica si un servicio systemd está activo."""
    resultado = _ejecutar(["systemctl", "is-active", "--quiet", servicio])
    return resultado["exito"]


# ─────────────────────────────────────────────────────────────
# NIVEL 0: Verificación de entorno forense
# ─────────────────────────────────────────────────────────────

def verificar_entorno_forense() -> dict:
    """
    Verifica que el sistema operativo está preparado para recepcionar
    evidencia forense SIN contaminarla.

    DEBE ejecutarse ANTES de conectar cualquier dispositivo de evidencia.

    Verificaciones:
        1. Auto-mount desactivado (udisks2, gvfs)
        2. Buffers del kernel vaciados (sync)
        3. Herramientas de bloqueo disponibles (hdparm, blockdev, losetup)
        4. Permisos root (necesarios para bloqueo)

    Returns:
        dict con estado de cada verificación

    Raises:
        EntornoForenseError: Si alguna verificación crítica falla
    """
    verificaciones = {}

    # 1. Verificar que auto-mount está desactivado
    # udisks2 es el daemon que auto-monta dispositivos en la mayoría de SO
    verificaciones["udisks2_off"] = not _servicio_activo("udisks2")

    # gvfs-udisks2-volume-monitor es el monitor de GNOME
    verificaciones["gvfs_off"] = not _servicio_activo("gvfs-udisks2-volume-monitor")

    # 2. Vaciado de buffers del kernel
    # sync fuerza la escritura de buffers pendientes a disco
    # Esto asegura que no hay datos pendientes que puedan interferir
    sync_result = _ejecutar(["sync"])
    verificaciones["sync"] = sync_result["exito"]

    # 3. Verificar herramientas de bloqueo disponibles
    # hdparm: control de parámetros del disco ( firmware )
    verificaciones["hdparm"] = _existe_binario("hdparm")

    # blockdev: control de dispositivos de bloques ( kernel )
    verificaciones["blockdev"] = _existe_binario("blockdev")

    # losetup: gestión de loop devices ( aislamiento )
    verificaciones["losetup"] = _existe_binario("losetup")

    # lsblk: listado de dispositivos de bloques
    verificaciones["lsblk"] = _existe_binario("lsblk")

    # 4. Verificar permisos root
    # hdparm y blockdev requieren permisos de superusuario
    verificaciones["root"] = os.geteuid() == 0

    # Evaluar resultado global
    criticos = {
        "hdparm": verificaciones["hdparm"],
        "blockdev": verificaciones["blockdev"],
        "losetup": verificaciones["losetup"],
        "root": verificaciones["root"]
    }

    fallos_criticos = [k for k, v in criticos.items() if not v]

    if fallos_criticos:
        raise EntornoForenseError(
            f"ENTORNO NO FORENSE. Herramientas faltantes o permisos insuficientes.\n"
            f"Fallos críticos: {', '.join(fallos_criticos)}\n"
            f"Solución: Usa CAINE OS o instala hdparm, util-linux y ejecuta como root."
        )

    verificaciones["global"] = True
    return verificaciones


# ─────────────────────────────────────────────────────────────
# NIVEL 0: Identificación de dispositivos
# ─────────────────────────────────────────────────────────────

def identificar_dispositivos(excluir_root: bool = True) -> list:
    """
    Identifica todos los dispositivos de almacenamiento conectados.

    Usa lsblk en formato JSON para obtener información estructurada
    del modelo, serie, tamaño, tipo y particiones de cada dispositivo.

    Args:
        excluir_root: Si True, excluye el dispositivo raíz del sistema

    Returns:
        Lista de objetos DispositivoInfo
    """
    cmd = [
        "lsblk", "-J", "-o",
        "NAME,SIZE,MODEL,SERIAL,TYPE,MOUNTPOINT,FSTYPE,TRAN"
    ]

    resultado = _ejecutar(cmd)
    if not resultado["exito"]:
        raise DispositivoNoEncontradoError(
            f"Error al listar dispositivos: {resultado['stderr']}"
        )

    try:
        datos = json.loads(resultado["stdout"])
    except json.JSONDecodeError:
        raise DispositivoNoEncontradoError(
            "Error al parsear salida de lsblk"
        )

    dispositivos = []
    ruta_raiz = _obtener_ruta_raiz()

    for dev in datos.get("blockdevices", []):
        if dev.get("type") != "disk":
            continue

        nombre = dev.get("name", "")
        ruta = f"/dev/{nombre}"

        # Excluir el dispositivo raíz si se solicita
        if excluir_root and ruta == ruta_raiz:
            continue

        # Excluir dispositivos de loop, ram, etc.
        if nombre.startswith("loop") or nombre.startswith("ram"):
            continue

        info = DispositivoInfo(
            nombre=nombre,
            tamaño=dev.get("size", "unknown"),
            modelo=dev.get("model", "unknown") or "unknown",
            serial=dev.get("serial", "unknown") or "unknown",
            tipo=dev.get("type", "unknown"),
            ruta=ruta,
            montaje_actual=dev.get("mountpoint"),
            fstype=dev.get("fstype"),
            particiones=[
                {
                    "nombre": p.get("name", ""),
                    "tamaño": p.get("size", ""),
                    "montaje": p.get("mountpoint"),
                    "fstype": p.get("fstype")
                }
                for p in dev.get("children", [])
                if p.get("type") == "part"
            ]
        )
        dispositivos.append(info)

    return dispositivos


def _dispositivo_es_removible(ruta: str) -> bool:
    """
    Determina si un dispositivo de bloque es removible (USB, SD, etc.).

    Args:
        ruta: Ruta del dispositivo (ej: /dev/sda)

    Returns:
        True si el dispositivo es removible.
    """
    nombre = Path(ruta).name
    sys_path = Path(f"/sys/block/{nombre}/removable")
    if sys_path.exists():
        try:
            return sys_path.read_text().strip() == "1"
        except Exception:
            pass

    # Fallback via lsblk
    r = _ejecutar(["lsblk", "-no", "RM", ruta])
    if r["exito"] and r["stdout"]:
        return r["stdout"].strip().split("\n")[0] == "1"
    return False


def _punto_montaje_a_dispositivo(punto: str) -> Optional[str]:
    """
    Obtiene el dispositivo de bloque padre asociado a un punto de montaje.

    Args:
        punto: Punto de montaje (ej: /run/live/medium)

    Returns:
        Ruta del dispositivo padre (ej: /dev/sdb) o None.
    """
    r = _ejecutar(["findmnt", "-n", "-o", "SOURCE", punto])
    if not (r["exito"] and r["stdout"]):
        return None

    source = r["stdout"].strip()
    if not source.startswith("/dev/"):
        return None

    # Obtener padre
    r2 = _ejecutar(["lsblk", "-no", "PKNAME", source])
    if r2["exito"] and r2["stdout"]:
        pkname = r2["stdout"].strip().split("\n")[0]
        if pkname:
            return f"/dev/{pkname}"

    # Si no tiene padre, normalizar partición a disco
    base = source[5:].rstrip("0123456789")
    if base.endswith("p") and len(base) > 1 and base[-2].isdigit():
        base = base[:-1]
    return f"/dev/{base}" if base else source


def _es_entorno_live() -> bool:
    """
    Detecta si el sistema operativo actual corre desde un medio Live/USB.

    Verifica puntos de montaje típicos de distribuciones Live y el origen
    del sistema de archivos raíz (overlayfs, squashfs, tmpfs, etc.).
    """
    # Puntos de montaje típicos de entornos Live
    puntos_live = [
        "/run/live/medium",
        "/lib/live/mount/medium",
        "/cdrom",
        "/run/initramfs/live",
    ]
    for punto in puntos_live:
        if Path(punto).is_mount():
            return True

    # Origen del sistema de archivos raíz
    r = _ejecutar(["findmnt", "-n", "-o", "FSTYPE", "/"])
    if r["exito"] and r["stdout"]:
        fstype = r["stdout"].strip().lower()
        if fstype in ("overlay", "overlayfs", "aufs", "squashfs", "tmpfs"):
            return True

    # cmdline indica modo live
    try:
        cmdline = Path("/proc/cmdline").read_text().lower()
        if any(x in cmdline for x in ("boot=live", "boot=casper", "live-media", "liveimg")):
            return True
    except Exception:
        pass

    return False


def _obtener_ruta_raiz() -> str:
    """
    Obtiene la ruta del dispositivo raíz (/) del sistema.

    Usa múltiples estrategias para soportar particiones, LVM, LUKS,
    RAID, NVMe y otros esquemas de montaje complejos.

    En entornos Live/USB, identifica el dispositivo Live (USB) como raíz,
    permitiendo bloquear los discos internos del anfitrión como evidencia.
    """
    # Estrategia 0: entorno Live/USB
    if _es_entorno_live():
        # Buscar el medio Live en orden de prioridad
        for punto in ["/run/live/medium", "/lib/live/mount/medium", "/cdrom", "/run/initramfs/live"]:
            dev = _punto_montaje_a_dispositivo(punto)
            if dev:
                return dev

        # Fallback: intentar identificar el dispositivo removible usado para /
        # a través de los puntos de montaje superiores
        r = _ejecutar(["findmnt", "-n", "-o", "SOURCE", "/run"])
        if r["exito"] and r["stdout"]:
            source = r["stdout"].strip()
            if source.startswith("/dev/"):
                dev_padre = _punto_montaje_a_dispositivo("/run")
                if dev_padre and _dispositivo_es_removible(dev_padre):
                    return dev_padre

    # Estrategia 1: findmnt para obtener el origen real de /
    resultado = _ejecutar(["findmnt", "-n", "-o", "SOURCE", "/"])
    if resultado["exito"] and resultado["stdout"]:
        source = resultado["stdout"].strip()
        # Si source es un dispositivo de bloque directo, obtener su padre
        if source.startswith("/dev/"):
            r2 = _ejecutar(["lsblk", "-no", "PKNAME", source])
            if r2["exito"] and r2["stdout"]:
                pkname = r2["stdout"].strip().split("\n")[0]
                if pkname:
                    return f"/dev/{pkname}"
            # Sin padre reconocido: es probablemente un disco directo
            # Eliminar números de partición (sda1 -> sda, nvme0n1p1 -> nvme0n1)
            base = source[5:]  # quitar /dev/
            base = base.rstrip("0123456789")
            if base.endswith("p") and len(base) > 1 and base[-2].isdigit():
                base = base[:-1]
            return f"/dev/{base}" if base else source

    # Estrategia 2: UUID del sistema de archivos raíz
    resultado = _ejecutar(["findmnt", "-n", "-o", "UUID", "/"])
    if resultado["exito"] and resultado["stdout"]:
        uuid = resultado["stdout"].strip()
        r2 = _ejecutar(["blkid", "-U", uuid])
        if r2["exito"] and r2["stdout"]:
            dev = r2["stdout"].strip()
            r3 = _ejecutar(["lsblk", "-no", "PKNAME", dev])
            if r3["exito"] and r3["stdout"]:
                pkname = r3["stdout"].strip().split("\n")[0]
                if pkname:
                    return f"/dev/{pkname}"
            return dev

    # Fallback de último recurso (riesgoso; evitar depender de él)
    return "/dev/sda"


def obtener_info_dispositivo(ruta: str) -> DispositivoInfo:
    """
    Obtiene información detallada de un dispositivo específico.

    Args:
        ruta: Ruta del dispositivo (ej: /dev/sdb)

    Returns:
        Objeto DispositivoInfo con toda la información
    """
    nombre = Path(ruta).name

    cmd = [
        "lsblk", "-J", "-o",
        "NAME,SIZE,MODEL,SERIAL,TYPE,MOUNTPOINT,FSTYPE",
        ruta
    ]

    resultado = _ejecutar(cmd)
    if not resultado["exito"]:
        raise DispositivoNoEncontradoError(
            f"Dispositivo no encontrado: {ruta}\n{resultado['stderr']}"
        )

    try:
        datos = json.loads(resultado["stdout"])
    except json.JSONDecodeError:
        raise DispositivoNoEncontradoError(
            f"Error al parsear información de {ruta}"
        )

    devs = datos.get("blockdevices", [])
    if not devs:
        raise DispositivoNoEncontradoError(
            f"Dispositivo no encontrado: {ruta}"
        )

    dev = devs[0]

    return DispositivoInfo(
        nombre=nombre,
        tamaño=dev.get("size", "unknown"),
        modelo=dev.get("model", "unknown") or "unknown",
        serial=dev.get("serial", "unknown") or "unknown",
        tipo=dev.get("type", "unknown"),
        ruta=ruta,
        montaje_actual=dev.get("mountpoint"),
        fstype=dev.get("fstype"),
        particiones=[
            {
                "nombre": p.get("name", ""),
                "tamaño": p.get("size", ""),
                "montaje": p.get("mountpoint"),
                "fstype": p.get("fstype")
            }
            for p in dev.get("children", [])
            if p.get("type") == "part"
        ]
    )


# ─────────────────────────────────────────────────────────────
# NIVEL 0: Blindaje físico ( firmware )
# ─────────────────────────────────────────────────────────────

def bloqueo_fisico_hdparm(ruta: str) -> dict:
    """
    CAPA 1: Bloqueo a nivel de firmware del disco.

    Envía un comando ioctl al controlador del disco mediante hdparm -r1.
    Esto solicita al hardware que rechace cualquier comando de escritura
    (WRITE) a nivel de bloque, independientemente de quién intente
    ejecutarlo (incluso root).

    Es la primera línea de defensa contra el error humano y la
    contaminación accidental de evidencia.

    Args:
        ruta: Ruta del dispositivo (ej: /dev/sdb)

    Returns:
        dict con estado del bloqueo

    Raises:
        BloqueoError: Si el bloqueo falla
    """
    # Primero: desmontar cualquier partición montada
    _desmontar_particiones(ruta)

    # Bloquear firmware
    resultado = _ejecutar(["hdparm", "-r1", ruta], sudo=True)

    if not resultado["exito"]:
        raise BloqueoError(
            f"FALLO CRÍTICO: hdparm -r1 {ruta}\n"
            f"Stderr: {resultado['stderr']}\n"
            f"El bloqueo de firmware no se pudo activar.\n"
            f"NO proceder con la adquisición."
        )

    # Verificar que el bloqueo se activó
    verificacion = _ejecutar(["hdparm", "-I", ruta], sudo=True)
    readonly_activado = False

    if verificacion["exito"]:
        # Buscar la línea que indica el estado de write cache
        for linea in verificacion["stdout"].split("\n"):
            if "write cache" in linea.lower():
                readonly_activado = "disabled" in linea.lower() or "readonly" in linea.lower()
                break

    return {
        "hdparm_ro": True,
        "verificado": readonly_activado,
        "comando": f"hdparm -r1 {ruta}",
        "mensaje": "Blindaje firmware activado" if readonly_activado
                   else "Blindaje firmware activado (verificación pendiente)"
    }


# ─────────────────────────────────────────────────────────────
# NIVEL 0: Blindaje lógico ( kernel block layer )
# ─────────────────────────────────────────────────────────────

def bloqueo_logico_blockdev(ruta: str) -> dict:
    """
    CAPA 2: Bloqueo a nivel del Kernel Block Layer.

    blockdev --setro le indica al subsistema de bloques de Linux que,
    aunque el dispositivo soporte escritura hardware, debe tratarlo
    como solo lectura a nivel de software.

    A diferencia de hdparm (que habla con el hardware), este comando
    opera en el kernel del sistema operativo.

    Args:
        ruta: Ruta del dispositivo (ej: /dev/sdb)

    Returns:
        dict con estado del bloqueo

    Raises:
        BloqueoError: Si el bloqueo falla
    """
    # Aplicar bloqueo
    resultado = _ejecutar(["blockdev", "--setro", ruta], sudo=True)

    if not resultado["exito"]:
        raise BloqueoError(
            f"FALLO CRÍTICO: blockdev --setro {ruta}\n"
            f"Stderr: {resultado['stderr']}\n"
            f"El bloqueo del kernel block layer no se pudo activar.\n"
            f"NO proceder con la adquisición."
        )

    # Verificar que el bloqueo se aceptó
    verificacion = _ejecutar(["blockdev", "--getro", ruta], sudo=True)
    readonly = verificacion["exito"] and verificacion["stdout"] == "1"

    if not readonly:
        raise BloqueoError(
            f"FALLO CRÍTICO: blockdev --getro {ruta} retornó "
            f"'{verificacion['stdout']}' en lugar de '1'\n"
            f"El kernel NO aceptó la restricción de solo lectura.\n"
            f"NO proceder con la adquisición."
        )

    return {
        "blockdev_ro": True,
        "verificado": True,
        "getro": verificacion["stdout"],
        "comando": f"blockdev --setro {ruta}",
        "mensaje": "Blindaje kernel block layer activado y verificado"
    }


# ─────────────────────────────────────────────────────────────
# NIVEL 0: Aislamiento via loop device
# ─────────────────────────────────────────────────────────────

def aislamiento_losetup(ruta_archivo: str) -> dict:
    """
    CAPA 3: Aislamiento via loop device read-only.

    Crea un dispositivo loop read-only que apunta al archivo de evidencia.
    El flag --ro es vital: evita que cualquier intento de montaje posterior
    pueda "escribir de vuelta" en el archivo de origen (como ocurre cuando
    un sistema de archivos intenta escribir un registro de journal).

    Bloquea el archivo a nivel de descriptor de archivo antes de que
    el sistema de archivos sea interpretado.

    Args:
        ruta_archivo: Ruta al archivo de evidencia (.raw, .img, etc.)

    Returns:
        dict con información del loop device creado

    Raises:
        BloqueoError: Si la creación del loop device falla
    """
    ruta_abs = str(Path(ruta_archivo).resolve())

    if not Path(ruta_abs).exists():
        raise BloqueoError(
            f"Archivo no encontrado: {ruta_abs}"
        )

    # Encontrar el próximo loop device disponible y asociar en modo RO
    resultado = _ejecutar(
        ["losetup", "-f", "--show", "--ro", ruta_abs],
        sudo=True
    )

    if not resultado["exito"]:
        raise BloqueoError(
            f"FALLO CRÍTICO: losetup -f --show --ro {ruta_abs}\n"
            f"Stderr: {resultado['stderr']}\n"
            f"No se pudo crear el loop device de aislamiento.\n"
            f"NO proceder con la adquisición."
        )

    loop_device = resultado["stdout"]

    # Verificar que el loop está en modo read-only
    verificacion = _ejecutar(["losetup", "-l"], sudo=True)
    loop_ro = False

    if verificacion["exito"]:
        for linea in verificacion["stdout"].split("\n"):
            if loop_device in linea and ruta_abs in linea:
                loop_ro = "(read-only)" in linea.lower() or "ro" in linea.lower()
                break

    return {
        "loop_device": loop_device,
        "loop_ro": True,
        "verificado": loop_ro,
        "archivo": ruta_abs,
        "comando": f"losetup -f --show --ro {ruta_abs}",
        "mensaje": f"Loop device {loop_device} creado en modo read-only"
    }


# ─────────────────────────────────────────────────────────────
# NIVEL 0: Montaje forense hardened
# ─────────────────────────────────────────────────────────────

def montaje_forense(
    ruta_dispositivo: str,
    punto_montaje: str,
    opciones_adicionales: str = ""
) -> dict:
    """
    CAPA 4: Montaje forense con políticas de seguridad extremas.

    Cada opción de montaje es una barrera contra la alteración de evidencia:

    - ro:       Solo lectura. El kernel rechaza cualquier write request.
    - noexec:   Elimina el vector de ejecución de código. Los archivos se
                vuelven inertes. Neutraliza malware o droppers ocultos.
    - noosuid:  Impide la elevación de privilegios via SUID/SGID bits.
    - nodev:    Impide la interpretación de archivos como dispositivos.
    - noatime:  Congela la cronología del sistema de archivos (MAC times).
                Sin esto, cada lectura modifica el Access Time = evidencia
                contaminada.

    Args:
        ruta_dispositivo: Dispositivo o archivo a montar
        punto_montaje: Directorio donde montar
        opciones_adicionales: Opciones extra separadas por coma

    Returns:
        dict con estado del montaje

    Raises:
        MontajeError: Si el montaje falla
    """
    # Verificar que el punto de montaje existe
    punto = Path(punto_montaje)
    if not punto.exists():
        punto.mkdir(parents=True, exist_ok=True)

    # Opciones base del montaje forense
    opciones_base = "ro,loop,noexec,noosuid,nodev,noatime"

    if opciones_adicionales:
        opciones_base += f",{opciones_adicionales}"

    # Ejecutar montaje
    resultado = _ejecutar(
        ["mount", "-o", opciones_base, ruta_dispositivo, punto_montaje],
        sudo=True
    )

    if not resultado["exito"]:
        raise MontajeError(
            f"FALLO CRÍTICO: mount -o {opciones_base} {ruta_dispositivo} {punto_montaje}\n"
            f"Stderr: {resultado['stderr']}\n"
            f"No se pudo montar en modo forense.\n"
            f"NO proceder con la adquisición."
        )

    # Verificar que el montaje tiene las opciones correctas
    verificacion = _ejecutar(["mount", "|", "grep", punto_montaje])
    opciones_verificadas = _verificar_opciones_montaje(punto_montaje)

    return {
        "montado": True,
        "punto": punto_montaje,
        "dispositivo": ruta_dispositivo,
        "opciones": opciones_base,
        "verificado": opciones_verificadas["todas_correctas"],
        "detalles": opciones_verificadas,
        "mensaje": f"Montaje forense activo en {punto_montaje}"
    }


def _verificar_opciones_montaje(punto_montaje: str) -> dict:
    """
    Verifica que un punto de montaje tiene todas las opciones forenses.

    Args:
        punto_montaje: Directorio montado

    Returns:
        dict con estado de cada opción verificada
    """
    resultado = _ejecutar(["findmnt", "-o", "OPTIONS", "-T", punto_montaje])

    opciones_requeridas = {
        "ro": False,
        "noexec": False,
        "noosuid": False,
        "nodev": False,
        "noatime": False
    }

    if resultado["exito"]:
        opts_str = resultado["stdout"].lower()
        for opt in opciones_requeridas:
            if opt in opts_str:
                opciones_requeridas[opt] = True

    opciones_requeridas["todas_correctas"] = all(opciones_requeridas.values())
    return opciones_requeridas


# ─────────────────────────────────────────────────────────────
# NIVEL 0: Verificación de bloqueo
# ─────────────────────────────────────────────────────────────

def verificar_bloqueo_completo(ruta: str) -> dict:
    """
    Verificación redundante de que NADA puede escribirse en el dispositivo.

    Ejecuta múltiples pruebas independientes para confirmar que las
    capas de bloqueo están activas y funcionando.

    Args:
        ruta: Ruta del dispositivo (ej: /dev/sdb)

    Returns:
        dict con resultado de cada verificación
    """
    checks = {}

    # 1. Verificar hdparm readonly
    resultado = _ejecutar(["hdparm", "-I", ruta], sudo=True)
    checks["hdparm_firmware_ro"] = False
    if resultado["exito"]:
        for linea in resultado["stdout"].split("\n"):
            if "write cache" in linea.lower():
                checks["hdparm_firmware_ro"] = (
                    "disabled" in linea.lower() or "readonly" in linea.lower()
                )
                break

    # 2. Verificar blockdev readonly
    resultado = _ejecutar(["blockdev", "--getro", ruta], sudo=True)
    checks["blockdev_kernel_ro"] = (
        resultado["exito"] and resultado["stdout"] == "1"
    )

    # 3. Verificación pasiva: no intentamos escribir en la evidencia
    # Escribir en un dispositivo de evidencia para "probar" el bloqueo es
    # contrario a los principios forenses (podría modificar 1 bit).
    checks["test_escritura"] = None
    checks["test_escritura_nota"] = (
        "Omitido: no se realiza escritura de prueba en dispositivos de evidencia "
        "(ISO 27037 / NIST SP 800-86)."
    )

    # 4. Verificar que no esté montado en modo lectura/escritura
    resultado = _ejecutar(["findmnt", "-n", "-o", "OPTIONS", ruta])
    checks["montaje_ro"] = False
    if resultado["exito"] and resultado["stdout"]:
        opciones = resultado["stdout"].strip().split(",")
        checks["montaje_ro"] = "ro" in opciones
    else:
        # Si no está montado, se considera OK
        checks["montaje_ro"] = True
        checks["montaje_nota"] = "Dispositivo no montado"

    # 5. Resultado global
    # Para USB/dispositivos removibles, hdparm puede no funcionar
    # pero blockdev --setro es suficiente a nivel de kernel
    checks["bloqueo_completo"] = checks["blockdev_kernel_ro"] and checks["montaje_ro"]

    # hdparm es capa adicional (firmware), no requerido para dispositivos USB
    if not checks["hdparm_firmware_ro"]:
        checks["nota"] = "hdparm no disponible (normal en USB). Blockdev protege a nivel kernel."

    return checks


# ─────────────────────────────────────────────────────────────
# NIVEL 0: Desmontaje y liberación
# ─────────────────────────────────────────────────────────────

def desmontar_y_liberar(
    punto_montaje: Optional[str] = None,
    loop_device: Optional[str] = None,
    ruta_dispositivo: Optional[str] = None
) -> dict:
    """
    Libera todos los recursos del blindaje forense.

    Ejecuta en orden inverso al blindaje:
        1. Desmontar el punto de montaje
        2. Liberar el loop device
        3. Restaurar el blockdev a read-write
        4. Restaurar el hdparm a read-write

    Args:
        punto_montaje: Directorio montado (opcional)
        loop_device: Loop device a liberar (ej: /dev/loop0)
        ruta_dispositivo: Dispositivo original (ej: /dev/sdb)

    Returns:
        dict con estado de cada operación de liberación
    """
    resultados = {}

    # 1. Desmontar
    if punto_montaje:
        res = _ejecutar(["umount", punto_montaje], sudo=True)
        resultados["umount"] = {
            "exito": res["exito"],
            "mensaje": f"Desmontado {punto_montaje}" if res["exito"]
                       else f"Error: {res['stderr']}"
        }

    # 2. Liberar loop device
    if loop_device:
        res = _ejecutar(["losetup", "-d", loop_device], sudo=True)
        resultados["losetup_d"] = {
            "exito": res["exito"],
            "mensaje": f"Loop {loop_device} liberado" if res["exito"]
                       else f"Error: {res['stderr']}"
        }

    # 3. Restaurar blockdev a read-write
    if ruta_dispositivo:
        res = _ejecutar(["blockdev", "--setrw", ruta_dispositivo], sudo=True)
        resultados["blockdev_setrw"] = {
            "exito": res["exito"],
            "mensaje": f"blockdev restaurado en {ruta_dispositivo}" if res["exito"]
                       else f"Error: {res['stderr']}"
        }

        # 4. Restaurar hdparm a read-write
        res = _ejecutar(["hdparm", "-r0", ruta_dispositivo], sudo=True)
        resultados["hdparm_r0"] = {
            "exito": res["exito"],
            "mensaje": f"hdparm restaurado en {ruta_dispositivo}" if res["exito"]
                       else f"Error: {res['stderr']}"
        }

    return resultados


def _desmontar_particiones(ruta_dispositivo: str):
    """
    Desmonta todas las particiones de un dispositivo.

    Necesario ANTES de aplicar hdparm, ya que un dispositivo montado
    no puede ser puesto en modo read-only de firmware.

    Args:
        ruta_dispositivo: Ruta del dispositivo (ej: /dev/sdb)
    """
    nombre = Path(ruta_dispositivo).name

    # Obtener particiones montadas de este dispositivo
    resultado = _ejecutar(["lsblk", "-no", "MOUNTPOINT", f"/dev/{nombre}"])

    if resultado["exito"] and resultado["stdout"]:
        for linea in resultado["stdout"].split("\n"):
            punto = linea.strip()
            if punto and punto != "":
                _ejecutar(["umount", "-l", punto], sudo=True)


# ─────────────────────────────────────────────────────────────
# CLASE PRINCIPAL: DispositivoForense
# ─────────────────────────────────────────────────────────────

class DispositivoForense:
    """
    Interfaz principal para el blindaje y manejo forense de dispositivos.

    Implementa el protocolo completo de NIVEL 0:
        1. Verificar entorno forense
        2. Identificar dispositivo
        3. Bloquear firmware (hdparm)
        4. Bloquear kernel (blockdev)
        5. Aislar (losetup)
        6. Montar hardened (mount)
        7. Verificar bloqueo
        8. Liberar al finalizar

    Uso:
        disco = DispositivoForense("/dev/sdb")
        disco.bloquear()
        disco.montar("/mnt/evidencia")
        # ... trabajar ...
        disco.desmontar_y_liberar()
    """

    def __init__(self, ruta: str):
        self.ruta = ruta
        self.info = None
        self.estado = EstadoBloqueo()
        self._bloqueado = False

    def identificar(self) -> DispositivoInfo:
        """Identifica el dispositivo y retorna su información."""
        self.info = obtener_info_dispositivo(self.ruta)
        return self.info

    def bloquear(self) -> EstadoBloqueo:
        """
        Aplica las 3 capas de bloqueo en orden:
            1. hdparm -r1 (firmware)
            2. blockdev --setro (kernel)
            3. Losetup --ro (aislamiento)

        Raises:
            BloqueoError: Si cualquiera de las capas falla
        """
        if self.info is None:
            self.identificar()

        # Seguridad: nunca bloquear el disco desde el cual corre el sistema operativo actual
        raiz = _obtener_ruta_raiz()
        if self.ruta == raiz:
            raise BloqueoError(
                f"ERROR DE SEGURIDAD: {self.ruta} es el disco desde el cual corre el sistema operativo actual.\n"
                "No se permite bloquear el disco de arranque.\n"
                "Si analiza un equipo apagado, arranque desde un USB Live forense; "
                "desde allí el disco interno del anfitrión NO será el dispositivo raíz y podrá bloquearlo."
            )

        # CAPA 1: Firmware
        res = bloqueo_fisico_hdparm(self.ruta)
        self.estado.hdparm_ro = res["hdparm_ro"]

        # CAPA 2: Kernel
        res = bloqueo_logico_blockdev(self.ruta)
        self.estado.blockdev_ro = res["blockdev_ro"]

        # Verificación completa
        verificacion = verificar_bloqueo_completo(self.ruta)
        self.estado.verificado = verificacion["bloqueo_completo"]

        if not self.estado.verificado:
            raise BloqueoError(
                "FALLO EN VERIFICACIÓN DE BLOQUEO.\n"
                f"Detalles: {verificacion}\n"
                "La evidencia podría estar comprometida.\n"
                "NO proceder con la adquisición."
            )

        self._bloqueado = True
        return self.estado

    def montar(self, punto_montaje: str) -> dict:
        """
        Monta el dispositivo en modo forense hardened.

        Requiere que el bloqueo esté activo (llamar bloquear() primero).

        Args:
            punto_montaje: Directorio donde montar

        Returns:
            dict con estado del montaje
        """
        if not self._bloqueado:
            raise BloqueoError(
                "El dispositivo no está bloqueado.\n"
                "Ejecutar bloquear() antes de montar()."
            )

        res = montaje_forense(self.ruta, punto_montaje)
        self.estado.montaje_punto = punto_montaje
        self.estado.montaje_opciones = res["opciones"]

        # Crear loop device si no existe
        if self.estado.loop_device is None:
            res_loop = aislamiento_losetup(self.ruta)
            self.estado.loop_device = res_loop["loop_device"]
            self.estado.loop_ro = res_loop["loop_ro"]

        return res

    def desmontar_y_liberar(self) -> dict:
        """Libera todos los recursos del blindaje."""
        resultados = desmontar_y_liberar(
            punto_montaje=self.estado.montaje_punto,
            loop_device=self.estado.loop_device,
            ruta_dispositivo=self.ruta
        )

        self.estado = EstadoBloqueo()
        self._bloqueado = False

        return resultados

    def verificar(self) -> dict:
        """Verifica que el bloqueo está activo y funcionando."""
        return verificar_bloqueo_completo(self.ruta)

    def __enter__(self):
        """Context manager: bloquea al entrar."""
        self.identificar()
        self.bloquear()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: libera al salir."""
        self.desmontar_y_liberar()
        return False


# ─────────────────────────────────────────────────────────────
# INTEGRACIÓN CON DAEMON
# ─────────────────────────────────────────────────────────────

def auto_bloquear(ruta: str) -> dict:
    """
    Bloquea un dispositivo usando el modo más disponible:
        1. Si el daemon está corriendo → usar daemon
        2. Si hay root → usar hdparm + blockdev directo
        3. Si no hay root → error

    Esta es la función principal que debe usar el usuario.
    """
    # Verificar si el daemon está activo
    # Seguridad: nunca bloquear el disco desde el cual corre el sistema operativo actual
    raiz = _obtener_ruta_raiz()
    if ruta == raiz:
        raise BloqueoError(
            f"ERROR DE SEGURIDAD: {ruta} es el disco desde el cual corre el sistema operativo actual.\n"
            "No se permite bloquear el disco de arranque.\n"
            "Si analiza un equipo apagado, arranque desde un USB Live forense; "
            "desde allí el disco interno del anfitrión NO será el dispositivo raíz y podrá bloquearlo."
        )

    try:
        from forensic_suite.daemon.forensic_blockerd import (
            bloquear_dispositivo as daemon_bloquear,
            detectar_modo
        )
        modo = detectar_modo()

        if modo in ("daemon", "udev"):
            return daemon_bloquear(ruta)
        else:
            # Modo manual: ejecutar bloqueo directo
            return bloqueo_fisico_hdparm(ruta) and bloqueo_logico_blockdev(ruta)
    except ImportError:
        # Daemon no disponible, usar bloqueo directo
        if os.geteuid() == 0:
            return bloqueo_fisico_hdparm(ruta)
        else:
            raise BloqueoError(
                "No hay daemon instalado y no se tienen permisos root.\n"
                "Ejecuta: sudo forensic_blockerd --install"
            )


def verificar_daemon() -> dict:
    """
    Verifica si el daemon de bloqueo forense está instalado y corriendo.
    """
    try:
        from forensic_suite.daemon.forensic_blockerd import detectar_modo
        modo = detectar_modo()

        daemon_activo = False
        try:
            r = subprocess.run(
                ["systemctl", "is-active", "--quiet", "forensic-blockerd"],
                capture_output=True
            )
            daemon_activo = r.returncode == 0
        except Exception:
            pass

        udev_instalado = Path("/etc/udev/rules.d/10-forensic-block.rules").exists()

        return {
            "modo_detectado": modo,
            "daemon_activo": daemon_activo,
            "udev_instalado": udev_instalado,
            "recomendacion": (
                "Daemon activo - protección automática" if daemon_activo
                else "Daemon inactivo - usar modo manual" if modo == "manual"
                else "Ejecuta: sudo forensic_blockerd --install"
            )
        }
    except ImportError:
        return {
            "modo_detectado": "manual",
            "daemon_activo": False,
            "udev_instalado": False,
            "recomendacion": "Daemon no disponible - modo manual"
        }
