"""
ForensicSuite Core - Modulos fundamentales del framework forense.

Modulos:
    - dispositivo: Blindaje del kernel (hdparm, blockdev, losetup, mount)
    - hasher: Hashes criptograficos (SHA-256, SHA-512, MD5)
    - perito: Configuracion del perito experto
    - cadena_custodia: Acta MP 2017 (6 secciones)
    - firma_gpg: Firma digital detached GPG
    - timestamp: Sello de tiempo RFC 3161
    - manifest: Manifest JSON canonico con verificacion
    - scalpel: File carving para recuperacion de evidencia
    - memoria: Adquisicion y analisis de memoria volatil (mforense)
"""

from forensic_suite.core.hasher import ForensicHasher
from forensic_suite.core.perito import PeritoConfig
from forensic_suite.core.cadena_custodia import CadenaCustodia
from forensic_suite.core.firma_gpg import ForensicGPG
from forensic_suite.core.timestamp import ForensicTimestamp
from forensic_suite.core.manifest import ForensicManifest
from forensic_suite.core.scalpel import ForensicScalpel
from forensic_suite.core.memoria import ForensicMemoria

__all__ = [
    "ForensicHasher",
    "PeritoConfig",
    "CadenaCustodia",
    "ForensicGPG",
    "ForensicTimestamp",
    "ForensicManifest",
    "ForensicScalpel",
    "ForensicMemoria",
]
