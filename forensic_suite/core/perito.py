"""
ForensicSuite - Perito: Configuración del Perito Experto
========================================================

Gestiona la configuración del perito experto en informática forense.

Esta configuración se utiliza en:
    - Cadena de custodia (Sección 2: COLECTOR)
    - Informes periciales (declaración del perito)
    - Firmas digitales GPG
    - Transferencia de evidencia

Campos del perito (formato MP 2017 / COPP Art. 224):
    - Nombre completo
    - Cédula de identidad
    - Título profesional
    - Tribunal de juramentación (opcional)
    - Número de juramentación (opcional)
    - Clave GPG (para firma digital)
    - URL de TSA (para sello de tiempo)
    - País de jurisdicción
    - Causa/numero de expediente

Protocolos de referencia:
    - COPP Art. 224: peritos designados y juramentados por el Juez
    - Manual Único de Cadena de Custodia (MP 2017)
    - ISO 27037: identificación del colector

Autor: Tr3w01
Versión: 1.0.0
"""

import getpass
import json
import os
import platform
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


# Ruta por defecto de la configuración
CONFIG_DIR = Path.home() / ".forensic_suite"
CONFIG_FILE = CONFIG_DIR / "perito.conf"


@dataclass
class PeritoConfig:
    """
    Configuración del perito experto en informática forense.

    Attributes:
        nombre: Nombre completo del perito
        cedula: Cédula de identidad (formato V-12.345.678 o E-12.345.678)
        titulo: Título profesional
        tribunal: Tribunal donde está juramentado
        juramentacion: Número de juramentación
        gpg_key: ID de la clave GPG (últimos 8+ caracteres)
        tsa_url: URL de la Autoridad de Tiempo (Timestamp Authority)
        pais: País de jurisdicción legal
        causa: Número de causa/expediente
        hash_algoritmo: Algoritmo primario de hash (sha256, sha512)
        cifrado: Algoritmo de cifrado (aes-256-cbc)
    """
    nombre: str = ""
    cedula: str = ""
    titulo: str = ""
    tribunal: str = ""
    juramentacion: str = ""
    gpg_key: str = ""
    tsa_url: str = "http://timestamp.digicert.com"
    pais: str = "venezuela"
    causa: str = ""
    hash_algoritmo: str = "sha256"
    cifrado: str = "aes-256-cbc"

    # Metadatos
    fecha_creacion: str = ""
    ultima_modificacion: str = ""
    hostname: str = ""
    usuario_sistema: str = ""

    def guardar(self, ruta: Optional[str] = None) -> str:
        """
        Guarda la configuración del perito en disco.

        El archivo se guarda en formato JSON canónico (ordenado de claves)
        para facilitar la verificación y auditoría.

        Args:
            ruta: Ruta del archivo de configuración (default: ~/.forensic_suite/perito.conf)

        Returns:
            Ruta del archivo guardado
        """
        if ruta is None:
            ruta = CONFIG_FILE
        else:
            ruta = Path(ruta)

        # Actualizar metadatos
        self.hostname = platform.node()
        self.usuario_sistema = getpass.getuser()

        if not self.fecha_creacion:
            self.fecha_creacion = datetime.now().isoformat()
        self.ultima_modificacion = datetime.now().isoformat()

        # Crear directorio si no existe (restringido al propietario)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(ruta.parent, 0o700)

        # Guardar en JSON canónico (sort_keys=True)
        datos = asdict(self)
        with open(ruta, "w", encoding="utf-8", opener=lambda path, flags: os.open(path, flags, 0o600)) as f:
            json.dump(datos, f, indent=2, sort_keys=True, ensure_ascii=False)

        return str(ruta)

    @classmethod
    def cargar(cls, ruta: Optional[str] = None) -> "PeritoConfig":
        """
        Carga la configuración del perito desde disco.

        Args:
            ruta: Ruta del archivo (default: ~/.forensic_suite/perito.conf)

        Returns:
            Objeto PeritoConfig con los datos cargados

        Raises:
            FileNotFoundError: Si el archivo no existe
            json.JSONDecodeError: Si el archivo tiene formato inválido
        """
        if ruta is None:
            ruta = CONFIG_FILE
        else:
            ruta = Path(ruta)

        if not ruta.exists():
            return cls()

        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)

        return cls(**datos)

    def verificar_gpg(self) -> dict:
        """
        Verifica que la clave GPG configurada existe y es válida.

        Returns:
            dict con estado de la verificación GPG
        """
        if not self.gpg_key:
            return {
                "configurado": False,
                "existe": False,
                "mensaje": "No hay clave GPG configurada"
            }

        try:
            resultado = subprocess.run(
                ["gpg", "--list-secret-keys", "--keyid-format", "LONG", self.gpg_key],
                capture_output=True,
                text=True,
                timeout=10
            )

            existe = resultado.returncode == 0 and self.gpg_key in resultado.stdout

            return {
                "configurado": True,
                "existe": existe,
                "key_id": self.gpg_key,
                "mensaje": f"Clave GPG {self.gpg_key} encontrada" if existe
                           else f"Clave GPG {self.gpg_key} NO encontrada"
            }

        except FileNotFoundError:
            return {
                "configurado": True,
                "existe": False,
                "mensaje": "GPG no está instalado en el sistema"
            }
        except subprocess.TimeoutExpired:
            return {
                "configurado": True,
                "existe": False,
                "mensaje": "Timeout al verificar GPG"
            }

    def es_valido(self) -> dict:
        """
        Valida que la configuración del perito tenga los campos mínimos.

        Returns:
            dict con estado de validación y campos faltantes
        """
        campos_requeridos = {
            "nombre": self.nombre,
            "cedula": self.cedula,
            "titulo": self.titulo
        }

        campos_opcionales = {
            "tribunal": self.tribunal,
            "juramentacion": self.juramentacion,
            "gpg_key": self.gpg_key
        }

        faltantes = [campo for campo, valor in campos_requeridos.items() if not valor]
        opcionales_faltantes = [campo for campo, valor in campos_opcionales.items() if not valor]

        return {
            "valido": len(faltantes) == 0,
            "campos_requeridos_faltantes": faltantes,
            "campos_opcionales_faltantes": opcionales_faltantes,
            "mensaje": "Configuración completa" if not faltantes
                       else f"Campos requeridos faltantes: {', '.join(faltantes)}"
        }

    def info_sistema(self) -> dict:
        """
        Retorna información del sistema donde se ejecuta la herramienta.

        Útil para documentar en cadena de custodia y manifiestos.

        Returns:
            dict con información del sistema
        """
        return {
            "hostname": platform.node(),
            "usuario": getpass.getuser(),
            "sistema_operativo": platform.system(),
            "arquitectura": platform.machine(),
            "kernel": platform.release(),
            "python": platform.python_version(),
            "timestamp": datetime.now().isoformat()
        }

    def __str__(self) -> str:
        """Representación legible de la configuración del perito."""
        lineas = [
            "=" * 60,
            "CONFIGURACIÓN DEL PERITO EXPERTO",
            "=" * 60,
            f"  Nombre:          {self.nombre or '(no configurado)'}",
            f"  Cédula:          {self.cedula or '(no configurado)'}",
            f"  Título:          {self.titulo or '(no configurado)'}",
            f"  Tribunal:        {self.tribunal or '(no especificado)'}",
            f"  Juramentación:   {self.juramentacion or '(no especificado)'}",
            f"  Clave GPG:       {self.gpg_key or '(no configurada)'}",
            f"  TSA URL:         {self.tsa_url}",
            f"  País:            {self.pais}",
            f"  Causa:           {self.causa or '(no especificada)'}",
            f"  Hash primario:   {self.hash_algoritmo}",
            f"  Cifrado:         {self.cifrado}",
            f"  hostname:        {platform.node()}",
            f"  usuario:         {getpass.getuser()}",
            "=" * 60
        ]
        return "\n".join(lineas)


def configurar_perito_interactivo() -> PeritoConfig:
    """
    Configura el perito de forma interactive (modo consola).

    Returns:
        Objeto PeritoConfig con los datos ingresados
    """
    print("=" * 60)
    print("CONFIGURACIÓN DEL PERITO EXPERTO")
    print("=" * 60)
    print()

    config = PeritoConfig()

    config.nombre = input("  Nombre completo: ").strip()
    config.cedula = input("  Cédula de identidad (ej: V-12.345.678): ").strip()
    config.titulo = input("  Título profesional: ").strip()
    config.tribunal = input("  Tribunal de juramentación (opcional): ").strip()
    config.juramentacion = input("  Número de juramentación (opcional): ").strip()
    config.gpg_key = input("  ID clave GPG (opcional): ").strip()
    config.tsa_url = input(f"  URL TSA [{config.tsa_url}]: ").strip() or config.tsa_url
    config.pais = input(f"  País [{config.pais}]: ").strip() or config.pais
    config.causa = input("  Número de causa/expediente (opcional): ").strip()

    print()
    print(config)

    guardar = input("\n  ¿Guardar configuración? (s/n): ").strip().lower()
    if guardar == "s":
        ruta = config.guardar()
        print(f"\n  Configuración guardada en: {ruta}")

    return config
