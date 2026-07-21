# 04 - Verificacion para Contra Peritaje

Guia para que un contra perito (experto designado por la defensa) pueda verificar de forma independiente que los resultados de ForensicSuite son correctos y no fueron manipulados.

## Principio fundamental

Todo resultado forense debe ser **reproducible**. Si el contra perito ejecuta los mismos comandos con los mismos datos, debe obtener los mismos resultados.

---

## Verificacion 1: Integridad de la herramienta

### Que verificar

Que el codigo fuente de ForensicSuite no fue alterado.

### Como verificar

```bash
# 1. Obtener el codigo fuente utilizado en la extraccion
# Debe estar proporcionado por el perito junto con los resultados

# 2. Verificar hashes del codigo fuente
forensic_suite hash forensic_suite/core/hasher.py
forensic_suite hash forensic_suite/core/dispositivo.py
forensic_suite hash forensic_suite/core/cadena_custodia.py

# 3. Comparar con los hashes registrados en el informe
forensic_suite verificar forensic_suite/core/hasher.py <hash_del_informe>

# 4. Revisar el codigo manualmente
# Los modulos clave son:
#   core/hasher.py        - lineas 66-113 (calcular_todos)
#   core/dispositivo.py   - lineas 93-120 (_ejecutar)
#   core/cadena_custodia.py - lineas 123-237 (crear_acta)
```

### Puntos criticos a revisar

- `hasher.py` linea 88-101: Los 3 hashes se calculan en la misma pasada de lectura
- `dispositivo.py` linea 105-119: subprocess con `capture_output=True`
- No hay conexion a internet durante el calculo de hashes
- No hay modificacion de archivos durante el proceso

---

## Verificacion 2: Hashes de evidencia

### Que verificar

Que los hashes SHA-256, SHA-512 y MD5 registrados son correctos.

### Como verificar con herramientas estandar

```bash
# Con sha256sum (incluido en todo Linux)
sha256sum evidence.raw

# Con sha512sum
sha512sum evidence.raw

# Con md5sum
md5sum evidence.raw

# Con OpenSSL
openssl dgst -sha256 evidence.raw
openssl dgst -sha512 evidence.raw
openssl dgst -md5 evidence.raw
```

### Cómo verificar con Python

```python
import hashlib

with open("evidence.raw", "rb") as f:
    sha256 = hashlib.sha256()
    sha512 = hashlib.sha512()
    md5 = hashlib.md5()
    while bloque := f.read(1048576):
        sha256.update(bloque)
        sha512.update(bloque)
        md5.update(bloque)

print(f"SHA-256: {sha256.hexdigest()}")
print(f"SHA-512: {sha512.hexdigest()}")
print(f"MD5:     {md5.hexdigest()}")
```

### Comparar

Los 3 valores deben coincidir exactamente con los registrados en:
- El acta de custodia (`.chain`)
- El archivo JSON de custodia (`.json`)
- El manifest (`.json`)

---

## Verificacion 3: Cadena de custodia

### Que verificar

Que el acta MP 2017 tiene las 6 secciones completas y correctas.

### Como verificar

```bash
# Leer el acta
cat evidence.raw.chain

# Cargar el JSON y verificar campos
python3 -c "
import json
with open('evidence.raw.json') as f:
    data = json.load(f)

# Verificar secciones presentes
campos = ['archivo', 'sha256', 'sha512', 'md5', 'tamano',
          'colector_nombre', 'colector_cedula',
          'receptor_nombre', 'receptor_fecha',
          'transferencias', 'cierre_fecha', 'cierre_disposicion']

for c in campos:
    valor = data.get(c, 'FALTANTE')
    print(f'  {c}: {valor}')
"
```

### Puntos criticos

1. **SHA-256 en el acta** debe coincidir con `sha256sum evidence.raw`
2. **Fecha de adquisicion** debe ser anterior a cualquier uso del archivo
3. **Nombre del perito** debe coincidir con la juramentacion
4. **Transferencias** deben documentar cada cambio de custodia

---

## Verificacion 4: Manifest de integridad

### Que verificar

Que el manifest.json no fue alterado y todos los archivos listados existen con los hashes correctos.

### Como verificar

```bash
# Usar el propio ForensicSuite
forensic_suite verificar-manifest manifest.json

# Verificar manualmente
python3 -c "
import json, hashlib
from pathlib import Path

with open('manifest.json') as f:
    data = json.load(f)

# Verificar hash del manifest
hash_256_original = data.get('manifest_sha256', '')
hash_512_original = data.get('manifest_sha512', '')

# Calcular hash del JSON sin los campos de hash
datos = data.copy()
datos.pop('manifest_sha256', None)
datos.pop('manifest_sha512', None)
json_str = json.dumps(datos, sort_keys=True, indent=2)

hash_256_calculado = hashlib.sha256(json_str.encode()).hexdigest()
hash_512_calculado = hashlib.sha512(json_str.encode()).hexdigest()

print(f'Manifest SHA-256: {\"VALIDO\" if hash_256_calculado == hash_256_original else \"INVALIDO\"} ')
print(f'Manifest SHA-512: {\"VALIDO\" if hash_512_calculado == hash_512_original else \"INVALIDO\"}')

# Verificar cada archivo
for arch in data.get('archivos', []):
    ruta = arch['ruta_absoluta']
    if not Path(ruta).exists():
        print(f'  FALTANTE: {arch[\"ruta_relativa\"]}')
        continue

    h = hashlib.sha256()
    with open(ruta, 'rb') as f:
        while b := f.read(1048576):
            h.update(b)
    coincide = h.hexdigest() == arch['sha256']
    print(f'  {arch[\"ruta_relativa\"]}: {\"OK\" if coincide else \"FALLA\"} ')
"
```

---

## Verificacion 5: Firma GPG

### Que verificar

Que la firma .asc es valida y corresponde al archivo.

### Como verificar

```bash
# Verificar firma con GPG
gpg --verify evidence.raw.asc evidence.raw

# Si es valido, GPG retorna exito (return code 0)
# Si falla, retorna error
```

### Que significa cada resultado

- `Good signature from "Nombre <email>"` → Firma valida
- `BAD signature` → Archivo fue modificado despues de firmar
- `No public key` → No se tiene la clave publica del firmante

---

## Verificacion 6: Sello de tiempo

### Que verificar

Que el token TSA es valido y contiene el hash correcto.

### Como verificar

```bash
# Verificar token TSA
openssl ts -verify -data evidence.raw -in evidence.raw.tsa.tsr

# Verificar y mostrar contenido
openssl ts -reply -in evidence.raw.tsa.tsr -text

# Verificar con hash especifico
openssl dgst -sha256 evidence.raw | openssl ts -verify -digest - -in evidence.raw.tsa.tsr
```

### Puntos criticos

1. El hash dentro del token TSA debe coincidir con el hash del archivo
2. La fecha del token debe ser coherente con la linea de tiempo del caso
3. El servidor TSA debe estar en la lista de servidores publicos reconocidos

---

## Verificacion 7: Bloqueo de escritura

### Que verificar

Que el dispositivo estaba en modo read-only durante la extraccion.

### Como verificar (si el dispositivo aun esta conectado)

```bash
# Verificar estado actual
hdparm -r /dev/sdX
blockdev --getro /dev/sdX

# Verificar en logs del sistema
dmesg | grep -i "read.only\|hdparm\|blockdev"
journalctl | grep -i "forensic"

# Verificar la regla udev
cat /etc/udev/rules.d/10-forensic-block.rules
udevadm test /sys/class/block/sdX
```

---

## Checklist del contra perito

| # | Verificacion | Herramienta | Resultado esperado |
|---|---|---|---|
| 1 | Codigo fuente no alterado | `forensic_suite hash` | Hashes coinciden |
| 2 | SHA-256 de evidencia | `sha256sum` | Coincide con acta |
| 3 | SHA-512 de evidencia | `sha512sum` | Coincide con acta |
| 4 | MD5 de evidencia | `md5sum` | Coincide con acta |
| 5 | Acta MP 2017 completa | Revision manual | 6 secciones |
| 6 | Manifest intacto | `verificar-manifest` | VALIDO |
| 7 | Firma GPG valida | `gpg --verify` | Good signature |
| 8 | Timestamp TSA valido | `openssl ts -verify` | OK |
| 9 | Bloqueo activo | `hdparm -r` | readonly = 1 |

## Si algo falla

1. Documentar exactamente que fallo
2. Ejecutar la verificacion de nuevo
3. Comparar con el resultado original
4. Si los hashes no coinciden, la evidencia esta comprometida
5. Notificar al juez de la discrepancia

## Nota sobre GPG

GPG no es un Proveedor de Servicios de Certificacion (PSC) acreditado por SUSCERTE en Venezuela. Para uso judicial, se recomienda:

1. Usar un PSC acreditado para firma y sello de tiempo
2. Si se usa GPG, documentar esta limitacion en el informe
3. El valor probatorio de GPG depende de la jurisdiccion
