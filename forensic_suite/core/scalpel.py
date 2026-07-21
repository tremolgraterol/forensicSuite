"""
ForensicSuite - Scalpel: File Carving para Recuperacion de Evidencia
====================================================================

Wrapper forense de Scalpel para recuperar archivos eliminados
de discos o imagenes forenses.

Scalpel busca archivos basandose en headers y footers conocidos
(file signatures) sin importar el filesystem subyacente.

Soporta: FAT16, FAT32, exFAT, NTFS, Ext2/3/4, JFS, XFS,
         ReiserFS, y partitions raw/forenses.

Uso forense:
    1. El disco DEBE estar bloqueado (blockdev --setro)
    2. Se ejecuta scalpel sobre el dispositivo montado o imagen
    3. Los archivos recuperados se hashean (SHA-256/SHA-512/MD5)
    4. Se genera manifest de integridad de archivos recuperados
    5. Se documenta en cadena de custodia

Autor: Tr3w01
Version: 1.0.0
"""

import hashlib
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone


SCALPEL_BIN = "/usr/bin/scalpel"
SCALPEL_CONF = "/etc/scalpel/scalpel.conf"

CONFIGS_DIR = Path(__file__).parent.parent / "configs"

PERFILES = {
    "recuperacion": "recuperacion.conf",
    "medios": "medios.conf",
    "documentos": "documentos.conf",
    "redes": "redes.conf",
    "cripto": "cripto.conf",
    "mensajeria": "mensajeria.conf",
    "general": "general.conf",
}


@dataclass
class ArchivoRecuperado:
    ruta: str
    nombre: str
    tipo: str
    tamano: int
    sha256: str
    sha512: str
    md5: str


@dataclass
class ResultadoCarving:
    exito: bool
    directorio_salida: str
    archivos_recuperados: list
    tipos_encontrados: dict
    total_archivos: int
    tamano_total: int
    tiempo_segundos: float
    mensaje: str


class ForensicScalpel:
    def __init__(
        self,
        scalpel_bin: str = SCALPEL_BIN,
        config_file: Optional[str] = None,
        perfil: Optional[str] = None
    ):
        self.scalpel_bin = scalpel_bin
        if perfil:
            if perfil not in PERFILES:
                raise ValueError(f"Perfil '{perfil}' no existe. Disponibles: {list(PERFILES.keys())}")
            self.config_file = str(CONFIGS_DIR / PERFILES[perfil])
        else:
            self.config_file = config_file or SCALPEL_CONF

    @staticmethod
    def listar_perfiles() -> dict:
        resultado = {}
        for nombre, archivo in PERFILES.items():
            ruta = CONFIGS_DIR / archivo
            existe = ruta.exists()
            tipos = 0
            if existe:
                try:
                    with open(ruta) as f:
                        for linea in f:
                            if not linea.startswith("#") and not linea.startswith("-") and linea.strip():
                                partes = linea.split()
                                if len(partes) >= 2:
                                    tipos += 1
                except Exception:
                    pass
            resultado[nombre] = {
                "archivo": str(ruta),
                "existe": existe,
                "tipos_configurados": tipos
            }
        return resultado

    def _ejecutar(self, args: list, timeout: int = 3600) -> dict:
        cmd = [self.scalpel_bin] + args
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            return {"ok": r.returncode == 0, "stdout": r.stdout,
                    "stderr": r.stderr, "code": r.returncode}
        except FileNotFoundError:
            return {"ok": False, "stdout": "", "stderr": "scalpel no encontrado", "code": -1}
        except subprocess.TimeoutExpired:
            return {"ok": False, "stdout": "", "stderr": "Timeout excedido", "code": -2}

    def verificar_instalacion(self) -> dict:
        if not os.path.exists(self.scalpel_bin):
            return {"instalado": False, "mensaje": "scalpel no encontrado en " + self.scalpel_bin}

        r = self._ejecutar(["-h"])
        version = ""
        for linea in (r["stdout"] + r["stderr"]).split("\n"):
            if "scalpel" in linea.lower() and "version" in linea.lower():
                version = linea.strip()
                break

        conf_ok = os.path.exists(self.config_file)

        return {
            "instalado": True,
            "binario": self.scalpel_bin,
            "version": version or "desconocida",
            "config": self.config_file,
            "config_existe": conf_ok,
            "mensaje": "Scalpel listo" if conf_ok else "Config no encontrado"
        }

    def listar_tipos(self) -> list:
        tipos = []
        if not os.path.exists(self.config_file):
            return tipos

        with open(self.config_file) as f:
            for linea in f:
                linea = linea.strip()
                if not linea or linea.startswith("#"):
                    continue
                partes = linea.split()
                if len(partes) >= 4:
                    tipos.append({
                        "extension": partes[0],
                        "case_sensitive": partes[1],
                        "max_size": partes[2],
                        "header": partes[3] if len(partes) > 3 else "",
                        "habilitado": True
                    })
        return tipos

    def _calcular_hashes(self, ruta: str) -> dict:
        sha256 = hashlib.sha256()
        sha512 = hashlib.sha512()
        md5 = hashlib.md5()
        tamano = 0

        with open(ruta, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
                sha512.update(chunk)
                md5.update(chunk)
                tamano += len(chunk)

        return {
            "sha256": sha256.hexdigest(),
            "sha512": sha512.hexdigest(),
            "md5": md5.hexdigest(),
            "tamano": tamano
        }

    def ejecutar_carving(
        self,
        fuente: str,
        directorio_salida: str,
        tipos: Optional[list[str]] = None,
        config_custom: Optional[str] = None,
        tamano_max: Optional[int] = None,
        verbose: bool = False
    ) -> ResultadoCarving:
        import time

        if not os.path.exists(fuente):
            return ResultadoCarving(
                exito=False, directorio_salida="", archivos_recuperados=[],
                tipos_encontrados={}, total_archivos=0, tamano_total=0,
                tiempo_segundos=0, mensaje=f"Fuente no encontrada: {fuente}"
            )

        os.makedirs(directorio_salida, exist_ok=True)

        args = ["-o", directorio_salida]

        if config_custom and os.path.exists(config_custom):
            args += ["-c", config_custom]
        elif self.config_file:
            args += ["-c", self.config_file]

        if verbose:
            args.append("-v")

        args.append(fuente)

        inicio = time.time()
        r = self._ejecutar(args, timeout=7200)
        tiempo = time.time() - inicio

        archivos = self._escanear_resultados(directorio_salida)
        tipos = {}
        tamano_total = 0
        for a in archivos:
            ext = a.tipo
            tipos[ext] = tipos.get(ext, 0) + 1
            tamano_total += a.tamano

        return ResultadoCarving(
            exito=r["ok"],
            directorio_salida=directorio_salida,
            archivos_recuperados=[vars(a) for a in archivos],
            tipos_encontrados=tipos,
            total_archivos=len(archivos),
            tamano_total=tamano_total,
            tiempo_segundos=tiempo,
            mensaje=f"Carving completado: {len(archivos)} archivos recuperados en {tiempo:.1f}s"
        )

    def _escanear_resultados(self, directorio: str) -> list[ArchivoRecuperado]:
        archivos = []
        dir_path = Path(directorio)

        if not dir_path.exists():
            return archivos

        for archivo in sorted(dir_path.rglob("*")):
            if not archivo.is_file():
                continue

            if archivo.name == "audit.txt":
                continue

            hashes = self._calcular_hashes(str(archivo))
            ext = archivo.suffix.lstrip(".") if archivo.suffix else "unknown"

            archivos.append(ArchivoRecuperado(
                ruta=str(archivo),
                nombre=archivo.name,
                tipo=ext,
                tamano=hashes["tamano"],
                sha256=hashes["sha256"],
                sha512=hashes["sha512"],
                md5=hashes["md5"]
            ))

        return archivos

    def generar_manifest_carving(
        self,
        directorio_salida: str,
        caso_id: str = "",
        perito: str = ""
    ) -> dict:
        import json
        import socket

        archivos = self._escanear_resultados(directorio_salida)
        if not archivos:
            return {"error": "No hay archivos recuperados"}

        manifest = {
            "version": "1.0",
            "tipo": "carving_manifest",
            "caso_id": caso_id,
            "perito": perito,
            "fecha_creacion": datetime.now(timezone.utc).isoformat(),
            "host": socket.gethostname(),
            "directorio_salida": directorio_salida,
            "total_archivos": len(archivos),
            "archivos": [vars(a) for a in archivos]
        }

        datos_str = json.dumps(manifest, sort_keys=True, indent=2)
        manifest["manifest_sha256"] = hashlib.sha256(datos_str.encode()).hexdigest()

        manifest_path = os.path.join(directorio_salida, "carving_manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)

        return manifest

    def analizar_audit(self, directorio_salida: str) -> dict:
        audit_path = os.path.join(directorio_salida, "audit.txt")
        if not os.path.exists(audit_path):
            return {"error": "audit.txt no encontrado"}

        stats = {"tipos": {}, "total": 0, "lineas_importantes": []}

        with open(audit_path) as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                if "files found" in linea.lower():
                    stats["lineas_importantes"].append(linea)
                elif "carved" in linea.lower():
                    stats["lineas_importantes"].append(linea)
                elif "." in linea and "/" not in linea:
                    ext = linea.split()[0] if linea.split() else ""
                    if ext:
                        stats["tipos"][ext] = stats["tipos"].get(ext, 0) + 1
                        stats["total"] += 1

        return stats
