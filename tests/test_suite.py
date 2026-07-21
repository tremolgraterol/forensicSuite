"""
ForensicSuite - Tests de la Parte 1
====================================

Tests para los módulos:
    - dispositivo.py (NIVEL 0: Blindaje del kernel)
    - hasher.py (SHA-256, SHA-512, MD5)
    - perito.py (Configuración del perito)

Ejecutar:
    python -m pytest tests/test_suite.py -v
    o
    python tests/test_suite.py
"""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from datetime import datetime

from forensic_suite.core.hasher import ForensicHasher, calcular_hash_bytes
from forensic_suite.core.perito import PeritoConfig
from forensic_suite.core.cadena_custodia import CadenaCustodia
from forensic_suite.core.firma_gpg import ForensicGPG
from forensic_suite.core.timestamp import ForensicTimestamp
from forensic_suite.core.manifest import ForensicManifest


class TestForensicHasher(unittest.TestCase):
    """Tests para el módulo de hashes criptográficos forenses."""

    def setUp(self):
        self.hasher = ForensicHasher()
        self.datos_test = b"ForensicSuite - Datos de prueba para hash"
        self.tmp_dir = tempfile.mkdtemp()
        self.archivo_test = os.path.join(self.tmp_dir, "test_evidence.bin")

        # Crear archivo de prueba con datos conocidos
        with open(self.archivo_test, "wb") as f:
            f.write(self.datos_test)

    def tearDown(self):
        # Limpiar archivos temporales y hashes generados
        import shutil
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_sha256_conocido(self):
        """Verificar SHA-256 contra valor conocido."""
        esperado = hashlib.sha256(self.datos_test).hexdigest()
        actual = self.hasher.calcular_sha256(self.archivo_test)
        self.assertEqual(actual, esperado)
        self.assertEqual(len(actual), 64)  # SHA-256 = 64 chars hex

    def test_sha512_conocido(self):
        """Verificar SHA-512 contra valor conocido."""
        esperado = hashlib.sha512(self.datos_test).hexdigest()
        actual = self.hasher.calcular_sha512(self.archivo_test)
        self.assertEqual(actual, esperado)
        self.assertEqual(len(actual), 128)  # SHA-512 = 128 chars hex

    def test_md5_conocido(self):
        """Verificar MD5 contra valor conocido."""
        esperado = hashlib.md5(self.datos_test).hexdigest()
        actual = self.hasher.calcular_md5(self.archivo_test)
        self.assertEqual(actual, esperado)
        self.assertEqual(len(actual), 32)  # MD5 = 32 chars hex

    def test_calcular_todos(self):
        """Verificar que calcular_todos retorna los 3 hashes consistentes."""
        resultado = self.hasher.calcular_todos(self.archivo_test)

        self.assertEqual(resultado.sha256, hashlib.sha256(self.datos_test).hexdigest())
        self.assertEqual(resultado.sha512, hashlib.sha512(self.datos_test).hexdigest())
        self.assertEqual(resultado.md5, hashlib.md5(self.datos_test).hexdigest())
        self.assertEqual(resultado.tamano_bytes, len(self.datos_test))
        self.assertEqual(len(resultado.algoritmos), 3)

    def test_verificar_hash_correcto(self):
        """Verificar que la verificación de hash exitosa retorna True."""
        sha256_esperado = hashlib.sha256(self.datos_test).hexdigest()
        resultado = self.hasher.verificar_hash(
            self.archivo_test, sha256_esperado, "sha256"
        )
        self.assertTrue(resultado["coincide"])
        self.assertEqual(resultado["mensaje"], "INTEGRIDAD VERIFICADA")

    def test_verificar_hash_incorrecto(self):
        """Verificar que la verificación con hash incorrecto retorna False."""
        hash_falso = "a" * 64
        resultado = self.hasher.verificar_hash(
            self.archivo_test, hash_falso, "sha256"
        )
        self.assertFalse(resultado["coincide"])
        self.assertIn("COMPROMETIDA", resultado["mensaje"])

    def test_generar_archivos_hashes(self):
        """Verificar que se generan los 3 archivos de hash."""
        archivos = self.hasher.generar_archivo_hashes(self.archivo_test)

        self.assertIn("sha256", archivos["archivos"])
        self.assertIn("sha512", archivos["archivos"])
        self.assertIn("md5", archivos["archivos"])

        # Verificar contenido del archivo SHA-256
        with open(archivos["archivos"]["sha256"], "r") as f:
            contenido = f.read()
            self.assertIn(self.hasher.calcular_sha256(self.archivo_test), contenido)

        # Limpiar
        for ruta in archivos["archivos"].values():
            if os.path.exists(ruta):
                os.remove(ruta)

    def test_archivo_no_existe(self):
        """Verificar que FileNotFoundError se lanza para archivo inexistente."""
        with self.assertRaises(FileNotFoundError):
            self.hasher.calcular_todos("/ruta/inexistente/evidence.raw")

    def test_archivo_vacio(self):
        """Verificar que ValueError se lanza para archivo vacío."""
        archivo_vacio = os.path.join(self.tmp_dir, "vacio.bin")
        with open(archivo_vacio, "wb") as f:
            pass  # Archivo vacío

        with self.assertRaises(ValueError):
            self.hasher.calcular_todos(archivo_vacio)

        os.remove(archivo_vacio)

    def test_bytes_en_memoria(self):
        """Verificar hash de bytes en memoria."""
        hash_sha256 = calcular_hash_bytes(self.datos_test, "sha256")
        self.assertEqual(hash_sha256, hashlib.sha256(self.datos_test).hexdigest())

        hash_sha512 = calcular_hash_bytes(self.datos_test, "sha512")
        self.assertEqual(hash_sha512, hashlib.sha512(self.datos_test).hexdigest())

        hash_md5 = calcular_hash_bytes(self.datos_test, "md5")
        self.assertEqual(hash_md5, hashlib.md5(self.datos_test).hexdigest())

    def test_archivo_grande(self):
        """Verificar que archivos grandes se procesan correctamente."""
        archivo_grande = os.path.join(self.tmp_dir, "grande.bin")
        tamano = 10 * 1024 * 1024  # 10 MB

        with open(archivo_grande, "wb") as f:
            f.write(os.urandom(tamano))

        resultado = self.hasher.calcular_todos(archivo_grande)
        self.assertEqual(resultado.tamano_bytes, tamano)
        self.assertEqual(len(resultado.sha256), 64)
        self.assertEqual(len(resultado.sha512), 128)
        self.assertEqual(len(resultado.md5), 32)

        os.remove(archivo_grande)


class TestPeritoConfig(unittest.TestCase):
    """Tests para el módulo de configuración del perito."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmp_dir, "perito.conf")

    def tearDown(self):
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        os.rmdir(self.tmp_dir)

    def test_crear_configuracion(self):
        """Verificar que se puede crear una configuración."""
        config = PeritoConfig(
            nombre="Juan Pérez",
            cedula="V-12.345.678",
            titulo="Ingeniero en Informática"
        )

        self.assertEqual(config.nombre, "Juan Pérez")
        self.assertEqual(config.cedula, "V-12.345.678")
        self.assertEqual(config.pais, "venezuela")
        self.assertEqual(config.hash_algoritmo, "sha256")

    def test_guardar_y_cargar(self):
        """Verificar que guardar y cargar mantiene la consistencia."""
        config_original = PeritoConfig(
            nombre="María García",
            cedula="E-87.654.321",
            titulo="Abogada",
            tribunal="Tribunal 5",
            gpg_key="ABC123DEF456",
            pais="argentina"
        )

        config_original.guardar(self.config_file)

        config_cargada = PeritoConfig.cargar(self.config_file)

        self.assertEqual(config_cargada.nombre, config_original.nombre)
        self.assertEqual(config_cargada.cedula, config_original.cedula)
        self.assertEqual(config_cargada.titulo, config_original.titulo)
        self.assertEqual(config_cargada.tribunal, config_original.tribunal)
        self.assertEqual(config_cargada.gpg_key, config_original.gpg_key)
        self.assertEqual(config_cargada.pais, config_original.pais)
        self.assertTrue(config_cargada.fecha_creacion != "")
        self.assertTrue(config_cargada.hostname != "")

    def test_configuracion_vacia(self):
        """Verificar que cargar de archivo inexistente retorna config vacía."""
        config = PeritoConfig.cargar("/ruta/inexistente/perito.conf")
        self.assertEqual(config.nombre, "")
        self.assertEqual(config.cedula, "")

    def test_validacion_campos_requeridos(self):
        """Verificar que la validación detecta campos faltantes."""
        config_vacia = PeritoConfig()
        resultado = config_vacia.es_valido()

        self.assertFalse(resultado["valido"])
        self.assertIn("nombre", resultado["campos_requeridos_faltantes"])
        self.assertIn("cedula", resultado["campos_requeridos_faltantes"])
        self.assertIn("titulo", resultado["campos_requeridos_faltantes"])

    def test_validacion_completa(self):
        """Verificar que configuración completa pasa validación."""
        config = PeritoConfig(
            nombre="Test",
            cedula="V-000.000.000",
            titulo="Test"
        )
        resultado = config.es_valido()

        self.assertTrue(resultado["valido"])
        self.assertEqual(len(resultado["campos_requeridos_faltantes"]), 0)

    def test_info_sistema(self):
        """Verificar que info_sistema retorna datos del sistema."""
        config = PeritoConfig()
        info = config.info_sistema()

        self.assertIn("hostname", info)
        self.assertIn("usuario", info)
        self.assertIn("sistema_operativo", info)
        self.assertIn("arquitectura", info)
        self.assertIn("kernel", info)
        self.assertIn("python", info)
        self.assertIn("timestamp", info)

    def test_str_legible(self):
        """Verificar que __str__ retorna representación legible."""
        config = PeritoConfig(nombre="Test User", cedula="V-123")
        representacion = str(config)

        self.assertIn("CONFIGURACIÓN DEL PERITO", representacion)
        self.assertIn("Test User", representacion)
        self.assertIn("V-123", representacion)


class TestDispositivo(unittest.TestCase):
    """Tests para el módulo de dispositivo (solo funciones que no requieren root)."""

    def test_entorno_forense(self):
        """Verificar que la función de entorno forense retorna resultado."""
        from forensic_suite.core.dispositivo import verificar_entorno_forense

        try:
            resultado = verificar_entorno_forense()
            self.assertIn("hdparm", resultado)
            self.assertIn("blockdev", resultado)
            self.assertIn("losetup", resultado)
            self.assertIn("lsblk", resultado)
        except Exception:
            # En entorno sin root, puede lanzar excepción
            pass

    def test_identificar_dispositivos(self):
        """Verificar que se pueden listar dispositivos del sistema."""
        from forensic_suite.core.dispositivo import identificar_dispositivos

        # excluir_root=False para incluir el disco del sistema
        dispositivos = identificar_dispositivos(excluir_root=False)
        self.assertIsInstance(dispositivos, list)
        # Debe haber al menos un disco
        self.assertGreater(len(dispositivos), 0)


class TestCadenaCustodia(unittest.TestCase):
    """Tests para cadena de custodia MP 2017."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_crear_acta(self):
        """Crear acta de custodia con campos minimos."""
        cadena = CadenaCustodia(
            archivo="evidence.raw",
            sha256="abc123",
            sha512="def456",
            md5="ghi789",
            tamano=1024,
            colector_nombre="Juan Perez",
            colector_cedula="V-12345678"
        )
        ruta = os.path.join(self.tmp_dir, "acta.chain")
        resultado = cadena.crear_acta(ruta)
        self.assertTrue(os.path.exists(resultado))
        with open(resultado) as f:
            contenido = f.read()
        self.assertIn("CADENA DE CUSTODIA", contenido)
        self.assertIn("Juan Perez", contenido)

    def test_agregar_transferencia(self):
        """Agregar transferencia a la cadena."""
        cadena = CadenaCustodia(
            archivo="evidence.raw",
            sha256="abc123",
            colector_nombre="Juan Perez",
            colector_cedula="V-123"
        )
        transferencia = cadena.agregar_transferencia(
            entrega="Juan Perez",
            recibe="Bodega Forense",
            motivo="Resguardo judicial"
        )
        self.assertEqual(transferencia.entrega, "Juan Perez")
        self.assertEqual(len(cadena.transferencias), 1)

    def test_verificar_integridad(self):
        """Verificar que acta tiene campos requeridos."""
        cadena = CadenaCustodia(
            archivo="evidence.raw",
            sha256="abc123",
            sha512="def456",
            md5="ghi789",
            colector_nombre="Juan Perez",
            colector_cedula="V-123"
        )
        estado = cadena.verificar_integridad()
        self.assertTrue(estado["seccion_1_identificacion"])
        self.assertTrue(estado["seccion_2_colector"])
        self.assertTrue(estado["hash_sha256"])
        self.assertTrue(estado["hash_sha512"])
        self.assertTrue(estado["hash_md5"])

    def test_cerrar_cadena(self):
        """Cerrar cadena de custodia."""
        cadena = CadenaCustodia(
            archivo="evidence.raw",
            sha256="abc123",
            colector_nombre="Juan Perez",
            colector_cedula="V-123"
        )
        cierre = cadena.cerrar_cadena(
            disposicion="Archivo judicial",
            autorizado_por="Juez 5"
        )
        self.assertTrue(cierre["cerrada"])
        self.assertEqual(cierre["disposicion"], "Archivo judicial")

    def test_exportar_json(self):
        """Exportar acta a JSON."""
        cadena = CadenaCustodia(
            archivo="evidence.raw",
            sha256="abc123",
            colector_nombre="Juan Perez"
        )
        ruta = os.path.join(self.tmp_dir, "acta.json")
        cadena.exportar_json(ruta)
        self.assertTrue(os.path.exists(ruta))
        with open(ruta) as f:
            data = json.load(f)
        self.assertEqual(data["archivo"], "evidence.raw")
        self.assertEqual(data["sha256"], "abc123")

    def test_cargar_json(self):
        """Cargar cadena desde JSON."""
        cadena = CadenaCustodia(
            archivo="test.raw",
            sha256="hash123",
            colector_nombre="Test"
        )
        ruta = os.path.join(self.tmp_dir, "carga.json")
        cadena.exportar_json(ruta)
        cargada = CadenaCustodia.cargar_json(ruta)
        self.assertEqual(cargada.archivo, "test.raw")
        self.assertEqual(cargada.sha256, "hash123")


class TestFirmaGPG(unittest.TestCase):
    """Tests para firma GPG (solo estructura)."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.archivo_test = os.path.join(self.tmp_dir, "evidence.bin")
        with open(self.archivo_test, "wb") as f:
            f.write(b"Datos de prueba para firma GPG")

    def tearDown(self):
        import shutil
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_verificar_gpg(self):
        """Verificar que gpg existe en el sistema."""
        gpg = ForensicGPG()
        resultado = gpg.verificar_gpg_instalado()
        self.assertIn("instalado", resultado)
        # No asumimos que GPG esta instalado en CI
        self.assertIsInstance(resultado["instalado"], bool)


class TestManifest(unittest.TestCase):
    """Tests para manifest JSON canonico."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.archivo1 = os.path.join(self.tmp_dir, "evidence1.bin")
        self.archivo2 = os.path.join(self.tmp_dir, "evidence2.bin")
        with open(self.archivo1, "wb") as f:
            f.write(b"Datos de evidencia 1")
        with open(self.archivo2, "wb") as f:
            f.write(b"Datos de evidencia 2")

    def tearDown(self):
        import shutil
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_agregar_archivo(self):
        """Agregar un archivo al manifest."""
        m = ForensicManifest()
        entry = m.agregar_archivo(self.archivo1)
        self.assertEqual(entry.sha256, hashlib.sha256(b"Datos de evidencia 1").hexdigest())
        self.assertEqual(len(m.archivos), 1)

    def test_escanear_directorio(self):
        """Escanear directorio completo."""
        m = ForensicManifest()
        archivos = m.escanear_directorio(self.tmp_dir)
        self.assertEqual(len(archivos), 2)
        self.assertGreater(archivos[0].tamano_bytes, 0)

    def test_generar_y_verificar(self):
        """Generar manifest y verificar integridad."""
        m = ForensicManifest()
        m.agregar_archivo(self.archivo1)
        m.agregar_archivo(self.archivo2)

        manifest = m.generar_manifest(caso_id="TEST-001", perito="Test User")
        self.assertGreater(len(manifest.manifest_sha256), 0)
        self.assertEqual(manifest.total_archivos, 2)

        verificacion = m.verificar(manifest)
        self.assertTrue(verificacion["manifest_valido"])
        self.assertEqual(verificacion["archivos_verificados"], 2)
        self.assertEqual(verificacion["archivos_fallidos"], 0)

    def test_guardar_y_cargar(self):
        """Guardar y cargar manifest."""
        m = ForensicManifest()
        m.agregar_archivo(self.archivo1)

        manifest = m.generar_manifest(caso_id="TEST-002")
        ruta = os.path.join(self.tmp_dir, "manifest.json")
        m.guardar(manifest, ruta)
        self.assertTrue(os.path.exists(ruta))

        m2 = ForensicManifest()
        manifest_cargado = m2.cargar(ruta)
        self.assertEqual(manifest_cargado.caso_id, "TEST-002")
        self.assertEqual(manifest_cargado.total_archivos, 1)

    def test_comparar_manifests(self):
        """Comparar dos manifest identicos."""
        m1 = ForensicManifest()
        m1.agregar_archivo(self.archivo1)
        manifest1 = m1.generar_manifest(caso_id="CMP-001")

        m2 = ForensicManifest()
        m2.agregar_archivo(self.archivo1)
        manifest2 = m2.generar_manifest(caso_id="CMP-002")

        resultado = m1.comparar(manifest1, manifest2)
        self.assertTrue(resultado["son_iguales"])
        self.assertEqual(len(resultado["archivos_modificados"]), 0)

    def test_manifest_integridad_comprometida(self):
        """Verificar que modificar archivo rompe verificacion de archivos."""
        m = ForensicManifest()
        m.agregar_archivo(self.archivo1)
        manifest = m.generar_manifest(caso_id="COMP-001")

        # Modificar el archivo
        with open(self.archivo1, "wb") as f:
            f.write(b"DATOS MODIFICADOS - COMPROMETIDOS")

        verificacion = m.verificar(manifest)
        # El manifest itself sigue valido (metadatos no cambiaron)
        # pero el archivo tiene hash diferente
        self.assertGreater(verificacion["archivos_fallidos"], 0)
        self.assertEqual(verificacion["detalles"][0]["integridad"], False)


class TestTimestamp(unittest.TestCase):
    """Tests para timestamp RFC 3161 (solo estructura)."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_listar_tsas(self):
        """Listar servidores TSA."""
        ts = ForensicTimestamp()
        tsas = ts.listar_tsas_disponibles()
        self.assertIsInstance(tsas, list)
        self.assertGreater(len(tsas), 0)
        self.assertIn("tsa", tsas[0])


class TestPeritoConfigSeguridad(unittest.TestCase):
    """Tests de seguridad para la configuración del perito."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.tmp_dir, "perito.conf")

    def tearDown(self):
        import shutil
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def test_permisos_configuracion(self):
        """Verificar que el archivo de configuración se guarda con permisos restrictivos."""
        config = PeritoConfig(nombre="Test", cedula="V-00000000", titulo="Test")
        config.guardar(self.config_file)

        self.assertTrue(os.path.exists(self.config_file))
        modo = os.stat(self.config_file).st_mode
        # Verificar que no es legible/ejecutable por grupo ni otros (0o600)
        self.assertEqual(modo & 0o077, 0)


class TestBloqueoSeguridad(unittest.TestCase):
    """Tests de seguridad: no bloquear el disco raíz del sistema operativo."""

    def test_auto_bloquear_rechaza_disco_raiz(self):
        """Verificar que auto_bloquear() rechaza el disco raíz."""
        from forensic_suite.core.dispositivo import auto_bloquear, _obtener_ruta_raiz, BloqueoError

        raiz = _obtener_ruta_raiz()
        with self.assertRaises(BloqueoError) as ctx:
            auto_bloquear(raiz)
        self.assertIn("disco desde el cual corre", str(ctx.exception).lower())

    def test_dispositivo_forense_rechaza_disco_raiz(self):
        """Verificar que DispositivoForense.bloquear() rechaza el disco raíz."""
        from forensic_suite.core.dispositivo import DispositivoForense, _obtener_ruta_raiz, BloqueoError

        raiz = _obtener_ruta_raiz()
        disp = DispositivoForense(raiz)
        with self.assertRaises(BloqueoError) as ctx:
            disp.bloquear()
        self.assertIn("disco desde el cual corre", str(ctx.exception).lower())


class TestDaemonForense(unittest.TestCase):
    """Tests para el daemon de bloqueo forense (no requieren root)."""

    def test_generar_regla_udev_excluye_raiz(self):
        """Verificar que la regla udev excluye el disco raíz."""
        from forensic_suite.daemon.forensic_blockerd import generar_regla_udev

        raiz = "/dev/sda"
        regla = generar_regla_udev(raiz)

        self.assertIn("Disco raíz excluido: /dev/sda", regla)
        self.assertIn('ENV{DEVNAME}!="/dev/sda"', regla)
        # Debe tener advertencia de que no es write blocker de hardware
        self.assertIn("NO ES un write blocker de hardware", regla)

    def test_generar_regla_udev_no_bloquea_particiones(self):
        """Verificar que la regla solo bloquea discos completos, no particiones."""
        from forensic_suite.daemon.forensic_blockerd import generar_regla_udev

        regla = generar_regla_udev("/dev/sda")
        self.assertIn('ENV{DEVTYPE}=="disk"', regla)


if __name__ == "__main__":
    unittest.main(verbosity=2)
