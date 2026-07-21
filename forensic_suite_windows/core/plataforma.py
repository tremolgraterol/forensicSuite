"""
ForensicSuite - Capa de abstraccion de plataforma
==================================================

Detecta si corre en Linux o Windows y provee funciones equivalentes
para listar dispositivos, verificar raiz y ejecutar comandos del sistema.

Autor: Tr3w01
Version: 1.0.0
"""

import os
import sys
import platform
import subprocess
from pathlib import Path
from typing import Optional, List, Dict


def es_windows() -> bool:
    """Retorna True si el sistema operativo es Windows."""
    return sys.platform.startswith("win")


def es_linux() -> bool:
    """Retorna True si el sistema operativo es Linux."""
    return sys.platform.startswith("linux")


def nombre_sistema() -> str:
    """Retorna un nombre legible del sistema operativo."""
    return platform.system()


def ejecutar(comando: List[str], sudo: bool = False, timeout: int = 10,
             shell: bool = False, capture: bool = True) -> Dict:
    """
    Ejecuta un comando del sistema de forma segura en Linux y Windows.
    En Windows ignora el parametro sudo.
    """
    if sudo and es_linux():
        comando = ["sudo"] + comando

    try:
        if capture:
            r = subprocess.run(
                comando,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=shell,
                encoding="utf-8",
                errors="replace"
            )
            return {
                "ok": r.returncode == 0,
                "stdout": r.stdout.strip(),
                "stderr": r.stderr.strip(),
                "code": r.returncode
            }
        else:
            r = subprocess.run(
                comando,
                timeout=timeout,
                shell=shell,
                encoding="utf-8",
                errors="replace"
            )
            return {
                "ok": r.returncode == 0,
                "stdout": "",
                "stderr": "",
                "code": r.returncode
            }
    except FileNotFoundError as e:
        return {
            "ok": False,
            "stdout": "",
            "stderr": f"Comando no encontrado: {comando[0]} ({e})",
            "code": 127
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "stdout": "",
            "stderr": f"Timeout ({timeout}s): {' '.join(comando)}",
            "code": 124
        }
    except Exception as e:
        return {
            "ok": False,
            "stdout": "",
            "stderr": str(e),
            "code": 1
        }


def _listar_dispositivos_windows() -> List[Dict]:
    """
    Lista discos fisicos conectados usando WMI/PowerShell.
    Retorna una estructura similar a lsblk para compatibilidad.
    """
    dispositivos = []
    ps_cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        "Get-Disk | Select-Object Number, FriendlyName, Size, HealthStatus, "
        "OperationalStatus, BusType, PartitionStyle | ConvertTo-Csv -NoTypeInformation"
    ]
    r = ejecutar(ps_cmd, timeout=20)
    if not r["ok"]:
        return dispositivos

    lineas = r["stdout"].splitlines()
    if len(lineas) < 2:
        return dispositivos

    encabezados = [h.strip().strip('"') for h in lineas[0].split(",")]
    for linea in lineas[1:]:
        valores = [v.strip().strip('"') for v in linea.split(",")]
        fila = dict(zip(encabezados, valores))
        try:
            tamano = int(fila.get("Size", 0))
        except ValueError:
            tamano = 0

        dispositivos.append({
            "name": f"Disk{fila.get('Number', '?')}",
            "type": "disk",
            "size": tamano,
            "model": fila.get("FriendlyName", "Desconocido"),
            "serial": "",
            "rm": False,
            "ro": False,
            "source": f"\\\\.\\PhysicalDrive{fila.get('Number', '?')}"
        })

    return dispositivos


def _listar_dispositivos_linux() -> List[Dict]:
    """Lista dispositivos usando lsblk en formato JSON."""
    import json
    r = ejecutar(["lsblk", "-J", "-o", "NAME,TYPE,SIZE,MODEL,SERIAL,RM,RO"], timeout=10)
    if not r["ok"]:
        return []
    try:
        data = json.loads(r["stdout"])
        return data.get("blockdevices", [])
    except json.JSONDecodeError:
        return []


def listar_dispositivos() -> List[Dict]:
    """Lista dispositivos de bloque disponibles en la plataforma actual."""
    if es_windows():
        return _listar_dispositivos_windows()
    return _listar_dispositivos_linux()


def dispositivo_raiz() -> Optional[str]:
    """
    Identifica el dispositivo raiz del sistema operativo actual.
    En Linux usa findmnt/lsblk. En Windows usa Get-Disk del disco del sistema.
    """
    if es_windows():
        # El disco del sistema suele ser C:, mapeado a PhysicalDrive0 normalmente
        r = ejecutar([
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-Partition | Where-Object {$_.DriveLetter -eq 'C'}).DiskNumber"
        ], timeout=10)
        if r["ok"] and r["stdout"].strip():
            return f"\\\\.\\PhysicalDrive{r['stdout'].strip()}"
        return "\\\\.\\PhysicalDrive0"

    # Linux: reutilizar logica existente de dispositivo.py si esta disponible
    try:
        from forensic_suite.core import dispositivo
        return dispositivo.dispositivo_raiz()
    except Exception:
        return None


def bloquear_posible_windows(ruta: str) -> Dict:
    """
    Intenta establecer proteccion contra escritura USB en Windows.
    NOTA: Windows no permite bloqueo selectivo por dispositivo de forma nativa
    sin driver de terceros. Esta funcion configura la politica de registro
    de proteccion contra escritura de dispositivos USB de almacenamiento.
    Requiere reinicio para que surta efecto.
    """
    if not es_windows():
        return {
            "ok": False,
            "error": "Esta funcion solo esta disponible en Windows"
        }

    r = ejecutar([
        "powershell",
        "-NoProfile",
        "-Command",
        "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\StorageDevicePolicies' "
        "-Name 'WriteProtect' -Value 1 -Type DWord -Force; "
        "New-Item -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\StorageDevicePolicies' -Force | Out-Null"
    ], sudo=False, timeout=20)

    return {
        "ok": r["ok"],
        "blockdev": r["ok"],
        "hdparm": False,
        "verificado": r["ok"],
        "error": r["stderr"] if not r["ok"] else None,
        "advertencia": (
            "Se activo proteccion contra escritura USB global del sistema. "
            "Requiere reinicio. Para desactivarla use forensic_suite desbloquear."
        ) if r["ok"] else None
    }


def desbloquear_posible_windows(ruta: str) -> Dict:
    """Desactiva la proteccion contra escritura USB global en Windows."""
    if not es_windows():
        return {
            "ok": False,
            "error": "Esta funcion solo esta disponible en Windows"
        }

    r = ejecutar([
        "powershell",
        "-NoProfile",
        "-Command",
        "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\StorageDevicePolicies' "
        "-Name 'WriteProtect' -Value 0 -Type DWord -Force"
    ], sudo=False, timeout=20)

    return {
        "ok": r["ok"],
        "blockdev": r["ok"],
        "hdparm": False,
        "error": r["stderr"] if not r["ok"] else None,
        "advertencia": "Requiere reinicio para que los cambios surtan efecto." if r["ok"] else None
    }
