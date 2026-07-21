"""
ForensicSuite - Hasher: Hashes Criptográficos Forenses
=====================================================

Implementa los 3 algoritmos de hash requeridos para integridad de evidencia:

    - SHA-256: Hash primario (ISO 27037, NIST SP 800-86)
    - SHA-512: Hash extendido (mayor margen de seguridad)
    - MD5:     Hash redundante (compatibilidad judicial)

Justificación de los 3 algoritmos:
    - SHA-256 es el estándar forense actual (64 caracteres hex, 256 bits)
    - SHA-512 ofrece 512 bits de seguridad (128 chars hex), mismo
      rendimiento que SHA-256 en hardware moderno de 64-bit
    - MD5 sigue siendo requerido por algunos sistemas judiciales
      a pesar de sus colisiones conocidas (usado como redundancia)

Protocolos de referencia:
    - ISO 27037: verificación de integridad de evidencia
    - NIST SP 800-86: sección 4.3.3 (data integrity)
    - FIPS 180-4: estándares SHA-2

Autor: Tr3w01
Versión: 1.0.0
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# Constantes
TAMANO_BLOQUE = 1024 * 1024  # 1 MB - tamaño de bloque para lectura


@dataclass
class HashResult:
    """Resultado del cálculo de hash para un archivo."""
    archivo: str
    sha256: str
    sha512: str
    md5: str
    tamano_bytes: int
    algoritmos: list


class ForensicHasher:
    """
    Calcula hashes criptográficos forenses usando 3 algoritmos.

    Cada archivo se procesa una sola vez con los 3 algoritmos
    simultáneamente para garantizar consistencia.

    Uso:
        hasher = ForensicHasher()
        resultado = hasher.calcular_todos("/path/to/evidence.raw")
        print(resultado.sha256)
        print(resultado.sha512)
        print(resultado.md5)
    """

    def __init__(self, tamano_bloque: int = TAMANO_BLOQUE):
        self.tamano_bloque = tamano_bloque

    def calcular_todos(self, ruta: str) -> HashResult:
        """
        Calcula SHA-256, SHA-512 y MD5 de un archivo en una sola pasada.

        Procesa el archivo en bloques de 1MB para manejar archivos
        de cualquier tamaño sin consumir toda la memoria.

        Args:
            ruta: Ruta al archivo a hashear

        Returns:
            Objeto HashResult con los 3 hashes

        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo está vacío
        """
        ruta_path = Path(ruta)

        if not ruta_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {ruta}")

        sha256 = hashlib.sha256()
        sha512 = hashlib.sha512()
        md5 = hashlib.md5()
        tamano_total = 0

        with open(ruta_path, "rb") as f:
            while True:
                bloque = f.read(self.tamano_bloque)
                if not bloque:
                    break
                sha256.update(bloque)
                sha512.update(bloque)
                md5.update(bloque)
                tamano_total += len(bloque)

        if tamano_total == 0:
            raise ValueError(f"Archivo vacío: {ruta}")

        return HashResult(
            archivo=str(ruta_path.resolve()),
            sha256=sha256.hexdigest(),
            sha512=sha512.hexdigest(),
            md5=md5.hexdigest(),
            tamano_bytes=tamano_total,
            algoritmos=["sha256", "sha512", "md5"]
        )

    def calcular_sha256(self, ruta: str) -> str:
        """
        Calcula solo SHA-256 de un archivo.

        Args:
            ruta: Ruta al archivo

        Returns:
            Hash SHA-256 en hexadecimal (64 caracteres)
        """
        sha256 = hashlib.sha256()
        with open(ruta, "rb") as f:
            while True:
                bloque = f.read(self.tamano_bloque)
                if not bloque:
                    break
                sha256.update(bloque)
        return sha256.hexdigest()

    def calcular_sha512(self, ruta: str) -> str:
        """
        Calcula solo SHA-512 de un archivo.

        Args:
            ruta: Ruta al archivo

        Returns:
            Hash SHA-512 en hexadecimal (128 caracteres)
        """
        sha512 = hashlib.sha512()
        with open(ruta, "rb") as f:
            while True:
                bloque = f.read(self.tamano_bloque)
                if not bloque:
                    break
                sha512.update(bloque)
        return sha512.hexdigest()

    def calcular_md5(self, ruta: str) -> str:
        """
        Calcula solo MD5 de un archivo.

        Args:
            ruta: Ruta al archivo

        Returns:
            Hash MD5 en hexadecimal (32 caracteres)
        """
        md5 = hashlib.md5()
        with open(ruta, "rb") as f:
            while True:
                bloque = f.read(self.tamano_bloque)
                if not bloque:
                    break
                md5.update(bloque)
        return md5.hexdigest()

    def verificar_hash(
        self,
        ruta: str,
        hash_esperado: str,
        algoritmo: str = "sha256"
    ) -> dict:
        """
        Verifica que el hash de un archivo coincida con uno conocido.

        Args:
            ruta: Ruta al archivo
            hash_esperado: Hash esperado (hex)
            algoritmo: "sha256", "sha512" o "md5"

        Returns:
            dict con resultado de verificación
        """
        hash_esperado = hash_esperado.lower().strip()

        if algoritmo == "sha256":
            hash_actual = self.calcular_sha256(ruta)
        elif algoritmo == "sha512":
            hash_actual = self.calcular_sha512(ruta)
        elif algoritmo == "md5":
            hash_actual = self.calcular_md5(ruta)
        else:
            raise ValueError(f"Algoritmo no soportado: {algoritmo}")

        coincide = hash_actual == hash_esperado

        return {
            "archivo": str(Path(ruta).resolve()),
            "algoritmo": algoritmo,
            "hash_esperado": hash_esperado,
            "hash_actual": hash_actual,
            "coincide": coincide,
            "mensaje": "INTEGRIDAD VERIFICADA" if coincide
                       else "INTEGRIDAD COMPROMETIDA - hashes no coinciden"
        }

    def generar_archivo_hashes(self, ruta: str, directorio: Optional[str] = None) -> dict:
        """
        Genera archivos de hashes seguros para evidencia forense.

        Crea archivos individuales .sha256, .sha512 y .md5 con el formato
        estándar "hash  nombre_archivo", los marca como solo lectura y
        opcionalmente genera un archivo .hash consolidado firmado con GPG.

        Args:
            ruta: Ruta al archivo de evidencia
            directorio: Directorio donde guardar

        Returns:
            dict con rutas de los archivos generados
        """
        import subprocess
        import os
        from datetime import datetime

        resultado = self.calcular_todos(ruta)
        ruta_path = Path(ruta)

        if directorio is None:
            directorio = ruta_path.parent

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        base = ruta_path.name

        # Generar archivos de hash individuales (formato estándar)
        archivos = {}
        hashes = {
            "sha256": resultado.sha256,
            "sha512": resultado.sha512,
            "md5": resultado.md5,
        }

        for algo, hash_val in hashes.items():
            ruta_hash = Path(directorio) / f"{base}.{algo}"
            if ruta_hash.exists():
                os.remove(ruta_hash)
            with open(ruta_hash, "w") as f:
                f.write(f"{hash_val}  {base}\n")
            os.chmod(ruta_hash, 0o444)
            archivos[algo] = str(ruta_hash)

        # Crear archivo .hash consolidado adicional (documentación + firma)
        ruta_hash_consolidado = Path(directorio) / f"{base}.hash"
        if ruta_hash_consolidado.exists():
            os.remove(ruta_hash_consolidado)

        with open(ruta_hash_consolidado, "w") as f:
            f.write(f"# ForensicSuite Hash Verification\n")
            f.write(f"# Fecha: {fecha}\n")
            f.write(f"# Archivo: {base}\n")
            f.write(f"# Tamano: {resultado.tamano_bytes} bytes\n")
            f.write(f"SHA256: {resultado.sha256}\n")
            f.write(f"SHA512: {resultado.sha512}\n")
            f.write(f"MD5: {resultado.md5}\n")
        os.chmod(ruta_hash_consolidado, 0o444)

        # Intentar firmar con GPG
        try:
            resultado_gpg = subprocess.run(
                ["gpg", "--batch", "--yes", "--detach-sign", str(ruta_hash_consolidado)],
                capture_output=True, text=True, timeout=30
            )
            if resultado_gpg.returncode == 0:
                archivos["firma"] = str(ruta_hash_consolidado) + ".sig"
        except Exception:
            pass  # GPG no disponible, continuar sin firma

        return {
            "archivos": archivos,
            "resultado": resultado,
            "ruta_hash": str(ruta_hash_consolidado)
        }

    def verificar_archivo_hashes(self, ruta_hash: str) -> dict:
        """
        Verifica un archivo .hash automaticamente.

        Lee el archivo .hash, recalcula los hashes del archivo original
        y compara.

        Args:
            ruta_hash: Ruta al archivo .hash

        Returns:
            dict con resultado de verificacion
        """
        import subprocess
        from datetime import datetime

        ruta_hash_path = Path(ruta_hash)

        if not ruta_hash_path.exists():
            return {"exito": False, "mensaje": "Archivo hash no encontrado"}

        # Leer archivo .hash
        hashes = {}
        metadata = {}
        with open(ruta_hash_path) as f:
            for linea in f:
                linea = linea.strip()
                if linea.startswith("#"):
                    if "Fecha:" in linea:
                        metadata["fecha"] = linea.split(":", 1)[1].strip()
                    elif "Archivo:" in linea:
                        metadata["archivo"] = linea.split(":", 1)[1].strip()
                elif linea.startswith("SHA256:"):
                    hashes["sha256"] = linea.split(":", 1)[1].strip()
                elif linea.startswith("SHA512:"):
                    hashes["sha512"] = linea.split(":", 1)[1].strip()
                elif linea.startswith("MD5:"):
                    hashes["md5"] = linea.split(":", 1)[1].strip()

        # Encontrar el archivo original
        ruta_original = ruta_hash_path.parent / metadata.get("archivo", "")
        if not ruta_original.exists():
            return {"exito": False, "mensaje": f"Archivo original no encontrado: {ruta_original}"}

        # Recalcular hashes
        resultado = self.calcular_todos(str(ruta_original))

        # Comparar
        verificaciones = {
            "sha256": resultado.sha256 == hashes.get("sha256"),
            "sha512": resultado.sha512 == hashes.get("sha512"),
            "md5": resultado.md5 == hashes.get("md5")
        }

        todos_validos = all(verificaciones.values())

        # Verificar firma GPG si existe
        firma_valida = None
        ruta_firma = Path(str(ruta_hash_path) + ".sig")
        if ruta_firma.exists():
            try:
                resultado_gpg = subprocess.run(
                    ["gpg", "--verify", str(ruta_firma), str(ruta_hash_path)],
                    capture_output=True, text=True, timeout=30
                )
                firma_valida = resultado_gpg.returncode == 0
            except Exception:
                firma_valida = False

        return {
            "exito": True,
            "archivo_original": str(ruta_original),
            "fecha_firma": metadata.get("fecha", "Desconocida"),
            "hashes_esperados": hashes,
            "hashes_actuales": {
                "sha256": resultado.sha256,
                "sha512": resultado.sha512,
                "md5": resultado.md5
            },
            "verificaciones": verificaciones,
            "todos_validos": todos_validos,
            "firma_gpg": firma_valida,
            "mensaje": "INTEGRIDAD VERIFICADA" if todos_validos else "INTEGRIDAD COMPROMETIDA"
        }


def calcular_hash_bytes(datos: bytes, algoritmo: str = "sha256") -> str:
    """
    Calcula hash de datos en memoria (sin archivo).

    Args:
        datos: Bytes a hashear
        algoritmo: "sha256", "sha512" o "md5"

    Returns:
        Hash en hexadecimal
    """
    h = hashlib.new(algoritmo)
    h.update(datos)
    return h.hexdigest()


def verificar_hash_linea(linea: str) -> dict:
    """
    Parsea y verifica una línea de formato hash (como las de sha256sum).

    Formato esperado: "HASH  filename"

    Args:
        línea: Línea del archivo de hash

    Returns:
        dict con hash y nombre de archivo
    """
    partes = linea.strip().split("  ", 1)
    if len(partes) != 2:
        raise ValueError(f"Formato de hash inválido: {linea}")

    return {
        "hash": partes[0].strip(),
        "archivo": partes[1].strip()
    }
