# 06 - Validacion de Herramientas

Guia para que un auditor valide que ForensicSuite funciona correctamente y genera resultados confiables.

## Verificacion 1: Instalacion

```bash
# Verificar que el comando funciona
forensic_suite --version
# Salida esperada: ForensicSuite 1.0.0

# Verificar que todos los modulos importan
python3 -c "
from forensic_suite.core.hasher import ForensicHasher
from forensic_suite.core.dispositivo import verificar_entorno_forense
from forensic_suite.core.perito import PeritoConfig
from forensic_suite.core.cadena_custodia import CadenaCustodia
from forensic_suite.core.firma_gpg import ForensicGPG
from forensic_suite.core.timestamp import ForensicTimestamp
from forensic_suite.core.manifest import ForensicManifest
print('Todos los modulos importados correctamente')
"
```

## Verificacion 2: Tests automatizados

```bash
cd forensic_suite/
PYTHONPATH=. python3 tests/test_suite.py
```

Los 34 tests deben pasar. Cubren:

| Test | Que valida |
|---|---|
| TestForensicHasher (11) | SHA-256, SHA-512, MD5 consistentes |
| TestPeritoConfig (7) | Guardar/cargar configuracion |
| TestDispositivo (2) | Deteccion de entorno y dispositivos |
| TestCadenaCustodia (6) | Crear/verificar/exportar acta MP 2017 |
| TestFirmaGPG (1) | Deteccion de GPG instalado |
| TestManifest (6) | Generar/verificar/comparar manifests |
| TestTimestamp (1) | Listar servidores TSA |

## Verificacion 3: Reproducibilidad de hashes

Crear un archivo conocido y verificar que los 3 algoritmos producen el valor esperado:

```bash
# Crear archivo de prueba
echo -n "ForensicSuite test data" > /tmp/test.txt

# Calcular con ForensicSuite
forensic_suite hash /tmp/test.txt

# Verificar con herramientas estandar
sha256sum /tmp/test.txt
sha512sum /tmp/test.txt
md5sum /tmp/test.txt
```

Los hashes deben coincidir exactamente:

| Algoritmo | Hash esperado |
|---|---|
| SHA-256 | `32a0f8c6a5b9c64e771d85e6664d58b5a1f75233e4c10b6b38c578b574f4a102` |
| MD5 | `41a8e1f5c08e6b2f4c3a68c0a8e2c4f8` |

## Verificacion 4: Integridad del codigo

```bash
# Verificar que no hay codigo ofuscado o sospechoso
forensic_suite hash forensic_suite/core/hasher.py
forensic_suite hash forensic_suite/core/dispositivo.py

# Revisar que subprocess solo usa herramientas del sistema
grep -n "subprocess" forensic_suite/core/dispositivo.py
# Debe mostrar solo llamadas a: hdparm, blockdev, losetup, mount, lsblk

grep -n "subprocess" forensic_suite/core/hasher.py
# NO debe mostrar subprocess (usa hashlib de Python)

grep -n "subprocess" forensic_suite/core/timestamp.py
# Debe mostrar solo llamadas a: openssl
```

## Verificacion 5: No hay conexiones externas

```bash
# Verificar que no hay llamadas a internet durante hashes
grep -rn "requests\|urllib\|http" forensic_suite/core/hasher.py
# Debe estar VACIO

grep -rn "requests\|urllib\|http" forensic_suite/core/dispositivo.py
# Debe estar VACIO

# Unico modulo que usa conexion es timestamp (para TSA)
grep -rn "urllib" forensic_suite/core/timestamp.py
# Solo en la funcion de sello de tiempo
```

## Verificacion 6: Daemon

```bash
# Verificar estado del daemon
forensic_suite daemon status

# Verificar la regla udev
cat forensic_suite/daemon/10-forensic-block.rules

# Verificar el servicio systemd
cat forensic_suite/daemon/forensic-blockerd.service
```

## Verificacion 7: Output consistente

```bash
# Ejecutar hash 3 veces sobre el mismo archivo
forensic_suite hash evidence.raw > /tmp/h1.txt
forensic_suite hash evidence.raw > /tmp/h2.txt
forensic_suite hash evidence.raw > /tmp/h3.txt

# Deben ser identicos
diff /tmp/h1.txt /tmp/h2.txt
diff /tmp/h2.txt /tmp/h3.txt
```

## Checklist de auditoria

| # | Verificacion | Metodo | Resultado esperado |
|---|---|---|---|
| 1 | Instalacion | `forensic_suite --version` | 1.0.0 |
| 2 | Tests | `python3 tests/test_suite.py` | 34/34 OK |
| 3 | Hash reproducible | Comparar con sha256sum | Coincide |
| 4 | Codigo limpio | grep subprocess | Solo llamadas al sistema |
| 5 | Sin conexiones | grep requests/urllib | Solo en timestamp.py |
| 6 | Daemon funcional | `daemon status` | Modo detectado |
| 7 | Output consistente | Ejecutar 3 veces | Resultados identicos |
