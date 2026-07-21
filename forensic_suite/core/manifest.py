"""
ForensicSuite - Manifest JSON Canónico
"""

import json
import hashlib
import os
from dataclasses import dataclass, asdict, field
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ArchivoManifest:
    ruta_relativa: str
    ruta_absoluta: str
    sha256: str
    sha512: str
    md5: str
    tamano_bytes: int
    tipo_mime: str
    permisos_octal: str
    fecha_hash: str


@dataclass
class ManifestData:
    version: str = "1.0"
    caso_id: str = ""
    perito: str = ""
    fecha_creacion: str = ""
    host: str = ""
    directorio_origen: str = ""
    total_archivos: int = 0
    total_bytes: int = 0
    archivos: list = field(default_factory=list)
    manifest_sha256: str = ""
    manifest_sha512: str = ""


class ForensicManifest:
    def __init__(self):
        self.archivos: list[ArchivoManifest] = []
        self.metadata: dict = {}

    def _hash_archivo(self, ruta: str) -> dict:
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

    def _tipo_mime(self, ruta: str) -> str:
        ext_map = {
            ".raw": "application/octet-stream",
            ".dd": "application/octet-stream",
            ".e01": "application/x-ewf",
            ".img": "application/octet-stream",
            ".iso": "application/x-iso9660-image",
            ".txt": "text/plain",
            ".json": "application/json",
            ".xml": "application/xml",
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".log": "text/plain",
        }
        ext = Path(ruta).suffix.lower()
        return ext_map.get(ext, "application/octet-stream")

    def _fecha_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def escanear_directorio(
        self,
        directorio: str,
        extensiones: Optional[list[str]] = None,
        excluidos: Optional[list[str]] = None
    ) -> list[ArchivoManifest]:
        dir_path = Path(directorio)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directorio no encontrado: {directorio}")

        excluidos = excluidos or []
        self.archivos = []

        for archivo in sorted(dir_path.rglob("*")):
            if not archivo.is_file():
                continue

            if any(ex in str(archivo) for ex in excluidos):
                continue

            if extensiones:
                if archivo.suffix.lower() not in extensiones:
                    continue

            hashes = self._hash_archivo(str(archivo))
            stat = archivo.stat()

            entry = ArchivoManifest(
                ruta_relativa=str(archivo.relative_to(dir_path)),
                ruta_absoluta=str(archivo.resolve()),
                sha256=hashes["sha256"],
                sha512=hashes["sha512"],
                md5=hashes["md5"],
                tamano_bytes=hashes["tamano"],
                tipo_mime=self._tipo_mime(str(archivo)),
                permisos_octal=oct(stat.st_mode)[-3:],
                fecha_hash=self._fecha_iso()
            )
            self.archivos.append(entry)

        return self.archivos

    def agregar_archivo(self, ruta: str) -> ArchivoManifest:
        archivo = Path(ruta)
        if not archivo.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

        hashes = self._hash_archivo(str(archivo))
        stat = archivo.stat()

        entry = ArchivoManifest(
            ruta_relativa=archivo.name,
            ruta_absoluta=str(archivo.resolve()),
            sha256=hashes["sha256"],
            sha512=hashes["sha512"],
            md5=hashes["md5"],
            tamano_bytes=hashes["tamano"],
            tipo_mime=self._tipo_mime(str(archivo)),
            permisos_octal=oct(stat.st_mode)[-3:],
            fecha_hash=self._fecha_iso()
        )
        self.archivos.append(entry)
        return entry

    def generar_manifest(
        self,
        caso_id: str = "",
        perito: str = "",
        directorio_origen: str = "",
        host: str = ""
    ) -> ManifestData:
        import socket
        total_bytes = sum(a.tamano_bytes for a in self.archivos)

        manifest = ManifestData(
            caso_id=caso_id,
            perito=perito,
            fecha_creacion=self._fecha_iso(),
            host=host or socket.gethostname(),
            directorio_origen=directorio_origen,
            total_archivos=len(self.archivos),
            total_bytes=total_bytes,
            archivos=[asdict(a) for a in self.archivos]
        )

        datos_sin_hash = asdict(manifest)
        datos_sin_hash.pop("manifest_sha256", None)
        datos_sin_hash.pop("manifest_sha512", None)

        json_str = json.dumps(datos_sin_hash, sort_keys=True, indent=2)
        manifest.manifest_sha256 = hashlib.sha256(json_str.encode()).hexdigest()
        manifest.manifest_sha512 = hashlib.sha512(json_str.encode()).hexdigest()

        return manifest

    def guardar(self, manifest: ManifestData, ruta_salida: str) -> str:
        data = asdict(manifest)
        json_str = json.dumps(data, sort_keys=True, indent=2)
        Path(ruta_salida).write_text(json_str, encoding="utf-8")
        return ruta_salida

    def cargar(self, ruta_manifest: str) -> ManifestData:
        data = json.loads(Path(ruta_manifest).read_text(encoding="utf-8"))
        return ManifestData(**{k: v for k, v in data.items()
                               if k in ManifestData.__dataclass_fields__})

    def verificar(self, manifest: ManifestData) -> dict:
        datos = asdict(manifest)
        hash_256_original = datos.pop("manifest_sha256", "")
        hash_512_original = datos.pop("manifest_sha512", "")

        json_str = json.dumps(datos, sort_keys=True, indent=2)
        hash_256_calculado = hashlib.sha256(json_str.encode()).hexdigest()
        hash_512_calculado = hashlib.sha512(json_str.encode()).hexdigest()

        integridad_256 = hash_256_calculado == hash_256_original
        integridad_512 = hash_512_calculado == hash_512_original

        archivos_ok = 0
        archivos_fail = 0
        detalles = []

        for arch in manifest.archivos:
            if Path(arch["ruta_absoluta"]).exists():
                hashes = self._hash_archivo(arch["ruta_absoluta"])
                ok = (hashes["sha256"] == arch["sha256"])
                if ok:
                    archivos_ok += 1
                else:
                    archivos_fail += 1
                detalles.append({
                    "archivo": arch["ruta_relativa"],
                    "integridad": ok,
                    "sha256_original": arch["sha256"][:16] + "...",
                    "sha256_actual": hashes["sha256"][:16] + "..."
                })
            else:
                archivos_fail += 1
                detalles.append({
                    "archivo": arch["ruta_relativa"],
                    "integridad": False,
                    "error": "Archivo no encontrado en disco"
                })

        return {
            "manifest_valido": integridad_256 and integridad_512,
            "integridad_manifest_256": integridad_256,
            "integridad_manifest_512": integridad_512,
            "archivos_verificados": archivos_ok,
            "archivos_fallidos": archivos_fail,
            "total_archivos": len(manifest.archivos),
            "detalles": detalles,
            "mensaje": "Manifest completo y verificado" if (integridad_256 and archivos_fail == 0)
                       else f"Issues: manifest={'OK' if integridad_256 else 'FAIL'}, "
                            f"archivos={archivos_fail} fallidos"
        }

    def comparar(self, manifest1: ManifestData, manifest2: ManifestData) -> dict:
        hashes1 = {a["ruta_relativa"]: a["sha256"] for a in manifest1.archivos}
        hashes2 = {a["ruta_relativa"]: a["sha256"] for a in manifest2.archivos}

        solo_en_1 = set(hashes1.keys()) - set(hashes2.keys())
        solo_en_2 = set(hashes2.keys()) - set(hashes1.keys())
        en_ambos = set(hashes1.keys()) & set(hashes2.keys())

        modificados = [k for k in en_ambos if hashes1[k] != hashes2[k]]
        identicos = len(en_ambos) - len(modificados)

        return {
            "archivos_identico": identicos,
            "archivos_modificados": modificados,
            "solo_en_primera": list(solo_en_1),
            "solo_en_segunda": list(solo_en_2),
            "total_primera": len(hashes1),
            "total_segunda": len(hashes2),
            "son_iguales": len(solo_en_1) == 0 and len(solo_en_2) == 0 and len(modificados) == 0,
            "mensaje": "Manifests idénticos" if len(solo_en_1) == 0 and len(solo_en_2) == 0 and len(modificados) == 0
                       else f"Diferencias: {len(solo_en_1)} solo en 1, {len(solo_en_2)} solo en 2, {len(modificados)} modificados"
        }
