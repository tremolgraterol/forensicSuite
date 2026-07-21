"""
ForensicSuite - Memoria: Adquisicion y Analisis de Memoria Volatil
===================================================================

Wrapper forense de mforense para adquisicion y analisis de memoria RAM.

Integra las herramientas:
- LiME (Linux Memory Extractor) - dump de memoria
- AVML (Microsoft) - dump alternativo
- Volatility3 - analisis forense de memoria

Protocolo:
1. Verificar entorno (root, LiME/AVML disponible)
2. Adquirir dump de memoria (mforense acquire)
3. Generar hashes (SHA-256/SHA-512/MD5)
4. Cadena de custodia
5. Analisis con Volatility (mforense analyze)

Autor: Tr3w01
Version: 1.0.0
"""

import os
import subprocess
from pathlib import Path
from typing import Optional


MFORENSE_BIN = Path(__file__).parent.parent / "daemon" / "mforense"


class ForensicMemoria:
    def __init__(self, mforense_bin: str = None):
        self.mforense_bin = str(mforense_bin or MFORENSE_BIN)

    def _ejecutar(self, args: list, timeout: int = 3600) -> dict:
        cmd = ["bash", self.mforense_bin] + args
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {"ok": r.returncode == 0, "stdout": r.stdout,
                    "stderr": r.stderr, "code": r.returncode}
        except FileNotFoundError:
            return {"ok": False, "stdout": "", "stderr": "mforense no encontrado", "code": -1}
        except subprocess.TimeoutExpired:
            return {"ok": False, "stdout": "", "stderr": "Timeout excedido", "code": -2}

    def verificar_entorno(self) -> dict:
        resultado = {
            "mforense": os.path.exists(self.mforense_bin),
            "root": os.geteuid() == 0,
            "lime": False,
            "avml": False,
            "volatility": False,
        }

        r = self._ejecutar(["--help"], timeout=10)
        if r["ok"] or "mforense" in r["stdout"].lower():
            resultado["mforense"] = True

        lime_path = f"/lib/modules/$(uname -r)/updates/dkms/lime.ko.xz"
        resultado["lime"] = os.path.exists(lime_path)

        try:
            subprocess.run(["avml", "--help"], capture_output=True, timeout=5)
            resultado["avml"] = True
        except Exception:
            pass

        try:
            subprocess.run(["volatility3", "--help"], capture_output=True, timeout=5)
            resultado["volatility"] = True
        except Exception:
            try:
                subprocess.run(["vol", "--help"], capture_output=True, timeout=5)
                resultado["volatility"] = True
            except Exception:
                pass

        return resultado

    def adquirir_memoria(
        self,
        directorio: str = ".",
        caso: str = "",
        herramienta: str = "auto"
    ) -> dict:
        args = ["acquire"]
        if caso:
            args.extend(["-c", caso])

        r = self._ejecutar(args, timeout=600)
        return {
            "exito": r["ok"],
            "salida": r["stdout"],
            "error": r["stderr"] if not r["ok"] else ""
        }

    def analizar_memoria(
        self,
        dump_file: str,
        plugin: str = "windows.pslist"
    ) -> dict:
        args = ["analyze", dump_file]
        if plugin:
            args.extend(["-p", plugin])

        r = self._ejecutar(args, timeout=1800)
        return {
            "exito": r["ok"],
            "salida": r["stdout"],
            "error": r["stderr"] if not r["ok"] else ""
        }

    def verificar_integridad(self, dump_file: str) -> dict:
        args = ["verify", dump_file]
        r = self._ejecutar(args, timeout=300)
        return {
            "exito": r["ok"],
            "salida": r["stdout"],
            "error": r["stderr"] if not r["ok"] else ""
        }

    def estado_caso(self, directorio: str = ".") -> dict:
        args = ["status"]
        r = self._ejecutar(args, timeout=30)
        return {
            "exito": r["ok"],
            "salida": r["stdout"],
            "error": r["stderr"] if not r["ok"] else ""
        }

    def cadena_custodia(self) -> dict:
        args = ["chain"]
        r = self._ejecutar(args, timeout=30)
        return {
            "exito": r["ok"],
            "salida": r["stdout"],
            "error": r["stderr"] if not r["ok"] else ""
        }

    def cifrar_evidencia(self, archivo: str) -> dict:
        args = ["cifrar", archivo]
        r = self._ejecutar(args, timeout=600)
        return {
            "exito": r["ok"],
            "salida": r["stdout"],
            "error": r["stderr"] if not r["ok"] else ""
        }

    def firmar_cadena(self, archivo: str) -> dict:
        args = ["firmar", archivo]
        r = self._ejecutar(args, timeout=120)
        return {
            "exito": r["ok"],
            "salida": r["stdout"],
            "error": r["stderr"] if not r["ok"] else ""
        }

    def generar_informe(self, directorio: str = ".") -> dict:
        args = ["report"]
        r = self._ejecutar(args, timeout=600)
        return {
            "exito": r["ok"],
            "salida": r["stdout"],
            "error": r["stderr"] if not r["ok"] else ""
        }
