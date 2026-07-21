"""
ForensicSuite - Cadena de Custodia: Formato MP 2017
===================================================

Implementa la cadena de custodia según el Manual Único de Cadena de Custodia
de Evidencias Físicas del Ministerio Público de Venezuela (2017).

Formato oficial con 6 secciones:
    1. IDENTIFICACIÓN DE LA EVIDENCIA
    2. COLECTOR
    3. TRANSPORTE
    4. RECEPTOR / ANALISTA
    5. TRANSFERENCIAS SUCESIVAS
    6. DEVOLUCIÓN O DESTRUCCIÓN

Marco legal:
    - COPP Art. 187: Cadena de custodia para evidencias digitales
    - COPP Art. 191: Prueba ilícita → nulidad absoluta
    - Manual Único de Cadena de Custodia (MP 2017)

Autor: Tr3w01
Versión: 1.0.0
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class Transferencia:
    """Una transferencia de custodia de evidencia."""
    numero: int
    fecha: str
    entrega: str
    recibe: str
    motivo: str
    firma: str = ""


@dataclass
class CadenaCustodia:
    """
    Cadena de custodia completa formato MP 2017.

    Attributes:
        archivo: Nombre del archivo de evidencia
        sha256: Hash SHA-256 del archivo
        sha512: Hash SHA-512 del archivo
        md5: Hash MD5 del archivo
        tamano: Tamaño del archivo (bytes)
        formato: Formato del archivo (raw, img, etc.)
        sistema_origen: Sistema donde se adquirió
        fecha_adquisicion: Fecha/hora de adquisición
        herramienta: Herramienta usada para adquirir
        colector_nombre: Nombre del perito colector
        colector_cedula: Cédula del perito
        colector_cargo: Cargo del perito
        colector_firma: Archivo de firma digital (.asc)
        transporte_medio: Medio de almacenamiento
        transporte_serie: Número de serie del medio
        transporte_ruta_origen: Ruta de origen
        transporte_ruta_destino: Ruta destino
        transporte_hash_recolector: Hash del binario recolector
        receptor_nombre: Nombre del receptor
        receptor_cedula: Cédula del receptor
        receptor_firma: Archivo de firma del receptor
        receptor_fecha: Fecha de recepción
        transferencias: Lista de transferencias
        cierre_fecha: Fecha de cierre
        cierre_disposicion: Disposición final
        cierre_autorizado_por: Autoridad que autoriza
        pais: País de jurisdicción
        protocolo: Protocolo de referencia
        referencia: Referencia del caso
    """
    # Sección 1: Identificación
    archivo: str = ""
    sha256: str = ""
    sha512: str = ""
    md5: str = ""
    tamano: int = 0
    formato: str = "raw"
    sistema_origen: str = ""
    fecha_adquisicion: str = ""
    herramienta: str = "ForensicSuite v1.0.0"

    # Sección 2: Colector
    colector_nombre: str = ""
    colector_cedula: str = ""
    colector_cargo: str = ""
    colector_firma: str = ""

    # Sección 3: Transporte
    transporte_medio: str = ""
    transporte_serie: str = ""
    transporte_ruta_origen: str = ""
    transporte_ruta_destino: str = ""
    transporte_hash_recolector: str = ""

    # Sección 4: Receptor
    receptor_nombre: str = ""
    receptor_cedula: str = ""
    receptor_firma: str = ""
    receptor_fecha: str = ""

    # Sección 5: Transferencias
    transferencias: list = field(default_factory=list)

    # Sección 6: Cierre
    cierre_fecha: str = ""
    cierre_disposicion: str = ""
    cierre_autorizado_por: str = ""

    # Metadatos
    pais: str = "venezuela"
    protocolo: str = "ISO 27037 / NIST SP 800-86 / RFC 3227"
    referencia: str = ""

    def crear_acta(self, ruta: str) -> str:
        """
        Genera el acta de cadena de custodia en formato Markdown.

        Args:
            ruta: Ruta donde guardar el archivo .chain

        Returns:
            Ruta del archivo generado
        """
        ahora = datetime.now().isoformat()

        # Actualizar fecha de adquisición si no está
        if not self.fecha_adquisicion:
            self.fecha_adquisicion = ahora

        # Actualizar receptor si no está
        if not self.receptor_nombre:
            self.receptor_nombre = self.colector_nombre
            self.receptor_cedula = self.colector_cedula
            self.receptor_fecha = self.fecha_adquisicion

        acta = f"""# ACTA DE CADENA DE CUSTODIA — EVIDENCIA DIGITAL
**Formato:** Manual Único de Cadena de Custodia (MP 2017)
**País legal:** {self.pais}
**Protocolo:** {self.protocolo}
**Referencia:** {self.referencia}
**Fecha de creación:** {ahora}

---

## 1. IDENTIFICACIÓN DE LA EVIDENCIA
| Campo | Valor |
|---|---|
| Archivo | {self.archivo} |
| SHA-256 | {self.sha256} |
| SHA-512 | {self.sha512} |
| MD5 | {self.md5} |
| Tamaño | {self._formatear_tamano()} |
| Formato | {self.formato} |
| Sistema origen | {self.sistema_origen} |
| Fecha/hora adquisición | {self.fecha_adquisicion} |
| Herramienta | {self.herramienta} |

---

## 2. COLECTOR
| Campo | Valor |
|---|---|
| Nombre | {self.colector_nombre} |
| Cédula | {self.colector_cedula} |
| Cargo | {self.colector_cargo} |
| Firma digital | {self.colector_firma} |

---

## 3. TRANSPORTE
| Campo | Valor |
|---|---|
| Medio de almacenamiento | {self.transporte_medio or '(por especificar)'} |
| Número de serie | {self.transporte_serie or '(por especificar)'} |
| Ruta origen | {self.transporte_ruta_origen or '(por especificar)'} |
| Ruta destino | {self.transporte_ruta_destino or '(por especificar)'} |
| Hash del recolector | {self.transporte_hash_recolector or '(verificado en adquisición)'} |

---

## 4. RECEPTOR / ANALISTA
| Campo | Valor |
|---|---|
| Nombre | {self.receptor_nombre} |
| Cédula | {self.receptor_cedula} |
| Firma digital | {self.receptor_firma} |
| Fecha recepción | {self.receptor_fecha} |

---

## 5. TRANSFERENCIAS SUCESIVAS
| # | Fecha | Entrega | Recibe | Motivo | Firma |
|---|---|---|---|---|---|
"""
        if self.transferencias:
            for t in self.transferencias:
                if isinstance(t, dict):
                    acta += f"| {t.get('numero', '')} | {t.get('fecha', '')} | {t.get('entrega', '')} | {t.get('recibe', '')} | {t.get('motivo', '')} | {t.get('firma', '')} |\n"
                else:
                    acta += f"| {t.numero} | {t.fecha} | {t.entrega} | {t.recibe} | {t.motivo} | {t.firma} |\n"
        else:
            acta += "| - | - | - | - | - | - |\n"

        acta += f"""
---

## 6. DEVOLUCIÓN O DESTRUCCIÓN
| Campo | Valor |
|---|---|
| Fecha | {self.cierre_fecha or '(pendiente)'} |
| Disposición final | {self.cierre_disposicion or '(pendiente)'} |
| Autorizado por | {self.cierre_autorizado_por or '(pendiente)'} |

---

*Documento generado por ForensicSuite v1.0.0*
*Fecha de generación: {ahora}*
*Nota: GPG no es un Proveedor de Servicios de Certificación (PSC) acreditado.*
*Para uso judicial, requerir certificado de PSC acreditado por SUSCERTE.*
"""

        # Guardar archivo
        ruta_path = Path(ruta)
        ruta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta_path, "w", encoding="utf-8") as f:
            f.write(acta)

        return str(ruta_path)

    def agregar_transferencia(
        self,
        entrega: str,
        recibe: str,
        motivo: str,
        firma: str = ""
    ) -> Transferencia:
        """
        Agrega una transferencia de custodia.

        Args:
            entrega: Quien entrega
            recibe: Quien recibe
            motivo: Motivo de la transferencia
            firma: Hash o archivo de firma

        Returns:
            Objeto Transferencia creado
        """
        numero = len(self.transferencias) + 1
        ahora = datetime.now().isoformat()

        transferencia = Transferencia(
            numero=numero,
            fecha=ahora,
            entrega=entrega,
            recibe=recibe,
            motivo=motivo,
            firma=firma
        )

        self.transferencias.append(asdict(transferencia))
        return transferencia

    def cerrar_cadena(
        self,
        disposicion: str,
        autorizado_por: str
    ) -> dict:
        """
        Cierra la cadena de custodia con la disposición final.

        COPP Art. 187: La cadena documenta todo el ciclo de vida.

        Args:
            disposicion: "Devolución", "Destrucción", "Archivo judicial"
            autorizado_por: Nombre de quien autoriza

        Returns:
            dict con estado del cierre
        """
        self.cierre_fecha = datetime.now().isoformat()
        self.cierre_disposicion = disposicion
        self.cierre_autorizado_por = autorizado_por

        return {
            "cerrada": True,
            "fecha": self.cierre_fecha,
            "disposicion": disposicion,
            "autorizado_por": autorizado_por,
            "mensaje": f"Cadena de custodia cerrada: {disposicion}"
        }

    def verificar_integridad(self) -> dict:
        """
        Verifica que la cadena de custodia esté completa.

        Returns:
            dict con estado de cada sección
        """
        checks = {
            "seccion_1_identificacion": bool(self.archivo and self.sha256),
            "seccion_2_colector": bool(self.colector_nombre and self.colector_cedula),
            "seccion_3_transporte": bool(self.transporte_medio),
            "seccion_4_receptor": bool(self.receptor_nombre),
            "seccion_5_transferencias": True,  # Opcional
            "seccion_6_cierre": bool(self.cierre_fecha and self.cierre_disposicion),
            "hash_sha256": bool(self.sha256),
            "hash_sha512": bool(self.sha512),
            "hash_md5": bool(self.md5)
        }

        checks["completa"] = all([
            checks["seccion_1_identificacion"],
            checks["seccion_2_colector"],
            checks["seccion_4_receptor"]
        ])

        return checks

    def exportar_json(self, ruta: str) -> str:
        """Exporta la cadena de custodia como JSON."""
        datos = asdict(self)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, sort_keys=True, ensure_ascii=False)
        return ruta

    @classmethod
    def cargar_json(cls, ruta: str) -> "CadenaCustodia":
        """Carga una cadena de custodia desde JSON."""
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
        return cls(**datos)

    def _formatear_tamano(self) -> str:
        """Formatea el tamaño en bytes a unidades legibles."""
        if self.tamano == 0:
            return "(desconocido)"
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if self.tamano < 1024:
                return f"{self.tamano:.2f} {unit}"
            self.tamano /= 1024
        return f"{self.tamano:.2f} PB"

    def __str__(self) -> str:
        """Representación legible."""
        estado = self.verificar_integridad()
        return (
            f"Cadena de Custodia: {self.archivo}\n"
            f"  Estado: {'COMPLETA' if estado['completa'] else 'INCOMPLETA'}\n"
            f"  SHA-256: {self.sha256[:32]}...\n"
            f"  Transferencias: {len(self.transferencias)}\n"
            f"  Cierre: {self.cierre_disposicion or 'pendiente'}"
        )
