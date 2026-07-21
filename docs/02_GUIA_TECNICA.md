# 02 - Guia Tecnica

## Arquitectura del sistema

```
forensic_suite/
  __main__.py           CLI principal (argparse)
  core/
    dispositivo.py      Blindaje del kernel (1020 lineas)
    hasher.py           SHA-256/SHA-512/MD5 (290 lineas)
    perito.py           Configuracion del perito (299 lineas)
    cadena_custodia.py  Acta MP 2017 (362 lineas)
    firma_gpg.py        Firma GPG detached (104 lineas)
    timestamp.py        Sello RFC 3161 (148 lineas)
    manifest.py         Manifest JSON canonico (189 lineas)
  daemon/
    forensic_blockerd.py     Daemon de bloqueo (715 lineas)
    forensic-blockerd.service  Unidad systemd
    10-forensic-block.rules    Regla udev
    forensic-block.conf       Configuracion JSON
```

## Bloqueo de escritura - Flujo tecnico

### Capa 1: hdparm (firmware)

```
hdparm -r1 /dev/sdX
```

Envia ioctl HDIO_SET_READONLY al controlador SCSI/SATA. Marca el bit de protection en el firmware del controlador. Cualquier intento de escritura es rechazado antes de llegar al kernel.

Verificacion:
```
hdparm -r /dev/sdX
# "readonly = 1 (on)" confirma que esta activo
```

### Capa 2: blockdev (kernel block layer)

```
blockdev --setro /dev/sdX
```

Establece el flag `FMODE_READONLY` en la estructura `block_device` del kernel. Cualquier intento de escritura retorna `-EROFS` (Read-Only File System).

Verificacion:
```
blockdev --getro /dev/sdX
# "1" = read-only activo
```

### Capa 3: losetup (aislamiento)

```
losetup --read-only --find --show /dev/sdX
```

Crea un device de bucle read-only. El kernel redirige todas las operaciones al dispositivo original pero bloquea escrituras. Ventaja: permite montar sin exponer el dispositivo original al filesystem.

### Capa 4: montaje forense

```
mount -o ro,loop,noexec,noosuid,nodev,noatime /dev/sdX /mnt/forense
```

Opciones de seguridad:
- `ro` → solo lectura
- `loop` → usa el loop device creado
- `noexec` → no ejecuta binarios
- `noosuid` → ignora bits SUID/SGID
- `nodev` → no interpreta devices especiales
- `noatime` → no actualiza tiempos de acceso

## Algoritmos de hash

### Calculo simultaneo

Los 3 hashes se calculan en una sola pasada del archivo:

```python
sha256 = hashlib.sha256()
sha512 = hashlib.sha512()
md5    = hashlib.md5()

with open(archivo, "rb") as f:
    while bloque := f.read(1048576):  # 1 MB
        sha256.update(bloque)
        sha512.update(bloque)
        md5.update(bloque)
```

Esto garantiza que los 3 hashes corresponden al exacto byte 0 al byte N del archivo, sin posibilidad de desfase.

### Por que 3 algoritmos

| Algoritmo | Tamano | Bits | Uso |
|---|---|---|---|
| SHA-256 | 64 hex chars | 256 | Estandar forense actual (ISO 27037) |
| SHA-512 | 128 hex chars | 512 | Seguridad extendida, mismo performance en 64-bit |
| MD5 | 32 hex chars | 128 | Redundancia, compatibilidad judicial legacy |

### Tamano de bloque

1 MB (1048576 bytes) por defecto. Permite manejar archivos de cualquier tamano sin consumir memoria completa. Un disco de 4TB se procesa con ~4MB de RAM.

## Cadena de custodia - Estructura MP 2017

### Seccion 1: Identificacion

Campos: archivo, SHA-256, SHA-512, MD5, tamano, formato, sistema origen, fecha/hora adquisicion, herramienta.

### Seccion 2: Colector

Campos: nombre, cedula, cargo, firma digital (.asc).

### Seccion 3: Transporte

Campos: medio de almacenamiento, numero de serie, ruta origen, ruta destino, hash del recolector.

### Seccion 4: Receptor / Analista

Campos: nombre, cedula, firma digital, fecha de recepcion.

### Seccion 5: Transferencias sucesivas

Tabla dinamica con: numero, fecha, quien entrega, quien recibe, motivo, firma.

### Seccion 6: Cierre

Campos: fecha, disposition final (devolucion/destruccion/archivo judicial), autorizado por.

## Manifest JSON canonico

### Generacion

1. Se escanea el directorio recursivamente
2. Para cada archivo se calcula SHA-256, SHA-512 y MD5
3. Se genera un JSON con metadatos + lista de archivos
4. Se calcula hash SHA-256 y SHA-512 del JSON mismo
5. Los hashes del JSON se insertan en el campo `manifest_sha256` / `manifest_sha512`

### Verificacion

1. Se carga el JSON
2. Se extraen los hashes del manifest (`manifest_sha256`, `manifest_sha512`)
3. Se recalculan los hashes del JSON sin esos campos
4. Se comparan: si coinciden, la estructura no fue alterada
5. Para cada archivo listado, se recalcula su SHA-256 y se compara con el registrado

## Firma GPG

```
gpg --batch --yes --detach-sign --armor \
    --local-user KEY_ID \
    --output evidence.raw.asc \
    evidence.raw
```

Genera un archivo `.asc` (ASCII-armored) con la firma detached. La firma:
- Prueba quien firmo (autenticidad)
- Se invalida si el archivo cambia (integridad)

Limitacion: GPG no es un PSC acreditado por SUSCERTE. Para uso judicial se requiere certificado de PSC acreditado.

## Sello de tiempo RFC 3161

1. Se calcula hash SHA-256 del archivo
2. Se envia `TimestampQuery` al servidor TSA (DigiCert, Sectigo, etc.)
3. El TSA retorna un `TimestampToken` firmado digitalmente
4. El token contiene: hash, fecha del servidor, firma del TSA
5. Verificacion: `openssl ts -reply -in token.tsr -verify`

TSA servers configurados:
- http://timestamp.digicert.com
- http://timestamp.sectigo.com
- http://timestamp.entrust.net/TSS/RFC3161sha2TS

## Daemon de bloqueo

### Modo daemon (systemd)

El daemon `forensic_blockerd.py` se ejecuta como servicio systemd con `Before=udisks2.service`. Cuando se detecta un nuevo dispositivo SD*, se ejecuta el bloqueo ANTES de que udisks2 lo monte automaticamente.

### Modo udev

Regla `10-forensic-block.rules` ejecuta `blockdev --setro` inmediatamente al detectar un dispositivo nuevo. El prefijo `10-` asegura que se ejecute ANTES de `80-udisks2.rules`.

### Modo manual

Ejecucion puntual: `sudo forensic_suite bloquear /dev/sdX`

### Auto-deteccion

El daemon detecta automaticamente:
- Si systemd+root esta disponible → daemon
- Si udev esta disponible → regla udev
- Si no → modo manual
