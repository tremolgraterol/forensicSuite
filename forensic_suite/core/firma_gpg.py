"""
ForensicSuite - Firma GPG: Firma Digital Detached
"""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FirmaResult:
    exito: bool
    archivo: str
    archivo_firma: str
    key_id: str
    mensaje: str


class ForensicGPG:
    def __init__(self, key_id: Optional[str] = None, gpg_bin: str = "gpg"):
        self.key_id = key_id
        self.gpg_bin = gpg_bin

    def _ejecutar(self, args: list, timeout: int = 60) -> dict:
        cmd = [self.gpg_bin] + args
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {"ok": r.returncode == 0, "stdout": r.stdout.strip(),
                    "stderr": r.stderr.strip(), "code": r.returncode}
        except FileNotFoundError:
            return {"ok": False, "stdout": "", "stderr": "gpg no encontrado", "code": -1}
        except subprocess.TimeoutExpired:
            return {"ok": False, "stdout": "", "stderr": "Timeout", "code": -2}

    def firmar(self, ruta_archivo: str, ruta_firma: Optional[str] = None) -> FirmaResult:
        ruta = Path(ruta_archivo)
        if not ruta.exists():
            return FirmaResult(False, str(ruta), "", "", f"No encontrado: {ruta_archivo}")

        if ruta_firma is None:
            ruta_firma = str(ruta) + ".asc"

        args = ["--batch", "--yes", "--detach-sign", "--armor"]
        if self.key_id:
            args += ["--local-user", self.key_id]
        args += ["--output", ruta_firma, str(ruta)]

        r = self._ejecutar(args)
        return FirmaResult(
            exito=r["ok"], archivo=str(ruta), archivo_firma=ruta_firma,
            key_id=self.key_id or "default",
            mensaje=f"Firma generada: {ruta_firma}" if r["ok"] else f"Error: {r['stderr']}"
        )

    def verificar(self, ruta_archivo: str, ruta_firma: Optional[str] = None) -> dict:
        ruta = Path(ruta_archivo)
        if ruta_firma is None:
            ruta_firma = str(ruta) + ".asc"

        if not Path(ruta_firma).exists():
            return {"verificado": False, "archivo": str(ruta), "firma": ruta_firma,
                    "mensaje": f"Firma no encontrada: {ruta_firma}"}

        r = self._ejecutar(["--verify", ruta_firma, str(ruta)])
        return {
            "verificado": r["ok"],
            "archivo": str(ruta),
            "firma": ruta_firma,
            "mensaje": "FIRMA VALIDA - Archivo no modificado" if r["ok"]
                       else "FIRMA INVALIDA - Archivo modificado",
            "info": r["stderr"] or r["stdout"]
        }

    def listar_claves(self) -> list:
        r = self._ejecutar(["--list-secret-keys", "--keyid-format", "LONG"])
        claves = []
        if r["ok"]:
            key_id_actual = None
            for linea in r["stdout"].split("\n"):
                if "sec" in linea:
                    partes = linea.split("/")
                    if len(partes) >= 2:
                        key_id_actual = partes[1].split(" ")[0]
                elif "uid" in linea and key_id_actual:
                    claves.append({"key_id": key_id_actual, "uid": linea.strip()})
                    key_id_actual = None
        return claves

    def verificar_gpg_instalado(self) -> dict:
        r = self._ejecutar(["--version"])
        return {
            "instalado": r["ok"],
            "version": r["stdout"].split("\n")[0] if r["ok"] else "",
            "mensaje": r["stdout"].split("\n")[0] if r["ok"] else "GPG no instalado"
        }
