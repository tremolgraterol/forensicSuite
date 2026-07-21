"""
ForensicSuite - Timestamp RFC 3161
"""

import base64
import subprocess
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import json


TSA_SERVERS = [
    "http://timestamp.digicert.com",
    "http://timestamp.sectigo.com",
    "http://timestamp.entrust.net/TSS/RFC3161sha2TS",
]


@dataclass
class TimestampResult:
    exito: bool
    archivo: str
    hash: str
    hash_algoritmo: str
    tsa: str
    fecha_timestamp: str
    token_b64: str
    archivo_token: str
    mensaje: str


class ForensicTimestamp:
    def __init__(self, tsa_server: Optional[str] = None, openssl_bin: str = "openssl"):
        self.tsa_server = tsa_server or TSA_SERVERS[0]
        self.tsa_server_list = TSA_SERVERS
        self.openssl_bin = openssl_bin

    def _ejecutar(self, args: list, timeout: int = 30, stdin_data: Optional[str] = None, binary: bool = False) -> dict:
        cmd = [self.openssl_bin] + args
        try:
            r = subprocess.run(cmd, capture_output=True, text=not binary, timeout=timeout,
                               input=stdin_data)
            stdout = r.stdout if binary else r.stdout.strip()
            stderr = r.stderr if binary else r.stderr.strip()
            return {"ok": r.returncode == 0, "stdout": stdout,
                    "stderr": stderr, "code": r.returncode}
        except FileNotFoundError:
            return {"ok": False, "stdout": b"" if binary else "", "stderr": "openssl no encontrado", "code": -1}
        except subprocess.TimeoutExpired:
            return {"ok": False, "stdout": b"" if binary else "", "stderr": "Timeout", "code": -2}

    def _calcular_hash_archivo(self, ruta: str, algoritmo: str = "sha256") -> str:
        h = hashlib.new(algoritmo)
        with open(ruta, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _query_ts(self, hash_hex: str, algoritmo: str = "sha256") -> Optional[bytes]:
        r = self._ejecutar([
            "ts", "-query", "-digest", hash_hex,
            "-no_nonce", "-cert"
        ], binary=True)
        if r["ok"] and r["stdout"]:
            return r["stdout"]
        return None

    def _request_timestamp(self, query_data: bytes, tsa: str) -> Optional[bytes]:
        import urllib.request
        import urllib.error
        try:
            req = urllib.request.Request(
                tsa, data=query_data,
                headers={"Content-Type": "application/timestamp-query"}
            )
            resp = urllib.request.urlopen(req, timeout=30)
            return resp.read()
        except Exception as e:
            return None

    def _parse_token(self, token_der: bytes) -> dict:
        try:
            # Write token to temp file for parsing
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tsr') as tmp:
                tmp.write(token_der)
                tmp_path = tmp.name
            
            r = self._ejecutar(["ts", "-reply", "-in", tmp_path,
                                 "-token_in", "-text"])
            
            # Clean up temp file
            import os
            os.unlink(tmp_path)
            
            if r["ok"]:
                fecha = ""
                for linea in r["stdout"].split("\n"):
                    if "time:" in linea.lower():
                        fecha = linea.split(":", 1)[1].strip() if ":" in linea else ""
                        break
                return {"ok": True, "texto": r["stdout"], "fecha": fecha}
        except Exception:
            pass
        return {"ok": False, "texto": "", "fecha": ""}

    def solicitar_timestamp(
        self,
        ruta_archivo: str,
        algoritmo: str = "sha256",
        ruta_token: Optional[str] = None,
        tsa_preferida: Optional[str] = None
    ) -> TimestampResult:
        ruta = Path(ruta_archivo)
        if not ruta.exists():
            return TimestampResult(False, str(ruta), "", "", "", "", "",
                                   "", f"No encontrado: {ruta_archivo}")

        hash_hex = self._calcular_hash_archivo(str(ruta), algoritmo)
        tsa = tsa_preferida or self.tsa_server

        query_data = self._query_ts(hash_hex, algoritmo)
        if not query_data:
            return TimestampResult(False, str(ruta), hash_hex, algoritmo, tsa, "", "",
                                   "", "No se pudo generar query TSA")

        token_der = self._request_timestamp(query_data, tsa)
        if not token_der:
            return TimestampResult(False, str(ruta), hash_hex, algoritmo, tsa, "", "",
                                   "", f"TSA {tsa} no respondio")

        token_b64 = base64.b64encode(token_der).decode("ascii")
        info = self._parse_token(token_der)
        fecha = info["fecha"] or datetime.now(timezone.utc).isoformat()

        if not ruta_token:
            ruta_token = str(ruta) + ".tsa.tsr"

        Path(ruta_token).write_bytes(token_der)

        return TimestampResult(True, str(ruta), hash_hex, algoritmo, tsa,
                               fecha, token_b64, ruta_token,
                               f"Timestamp RFC 3161 obtenido de {tsa}")

    def verificar_timestamp(self, ruta_token: str) -> dict:
        r = self._ejecutar(["ts", "-reply", "-in", ruta_token, "-text"])
        return {
            "valido": r["ok"],
            "texto": r["stdout"],
            "mensaje": "Timestamp verificado correctamente" if r["ok"]
                       else f"Error verificacion: {r['stderr']}"
        }

    def verificar_con_hash(self, ruta_token: str, hash_esperado: str) -> dict:
        info = self._ejecutar(["ts", "-reply", "-in", ruta_token, "-text"])
        hash_coincide = hash_esperado in (info["stdout"] or "") if info["ok"] else False
        verificacion = self.verificar_timestamp(ruta_token)
        return {
            "hash_coincide": hash_coincide,
            "verificacion_firma": verificacion["valido"],
            "valido": hash_coincide and verificacion["valido"],
            "mensaje": "Timestamp valido y hash coincide" if hash_coincide and verificacion["valido"]
                       else "Timestamp o hash invalido"
        }

    def listar_tsas_disponibles(self) -> list:
        resultados = []
        for tsa in self.tsa_server_list:
            try:
                import urllib.request
                req = urllib.request.Request(tsa, method="HEAD")
                urllib.request.urlopen(req, timeout=5)
                resultados.append({"tsa": tsa, "disponible": True})
            except Exception:
                resultados.append({"tsa": tsa, "disponible": False})
        return resultados
