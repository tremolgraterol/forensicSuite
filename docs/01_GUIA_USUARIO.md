# 01 - Guia de Usuario

## Requisitos

- Python 3.9 o superior
- Linux (tested on Ubuntu/Debian)
- GPG instalado (para firmas digitales)
- OpenSSL (para sellos de tiempo RFC 3161)
- Permisos root solo para bloqueo de dispositivos

## Instalacion

```bash
cd forensic_suite/
./install.sh
```

Despues de instalar, ejecutar `forensic_suite` o `fs` desde cualquier terminal.

## Flujo de trabajo tipico

### Paso 1: Configurar el perito

```bash
forensic_suite perito --configurar
```

Esto crea `~/.forensic_suite/perito.conf` con nombre, cedula, titulo y clave GPG.

### Paso 2: Conectar el disco y bloquear

```bash
# Listar discos disponibles
forensic_suite listar

# Bloquear escritura (requiere root)
sudo forensic_suite bloquear /dev/sdb
```

El bloqueo aplica 4 capas de proteccion:
- `hdparm -r1` → firmware
- `blockdev --setro` → kernel block layer
- Loop device read-only → aislamiento
- Montaje con opciones `ro,noexec,nodev`

### Paso 3: Calcular hashes

```bash
forensic_suite hash /mnt/forense/evidence.raw
```

Salida:
```
Archivo:   /mnt/forense/evidence.raw
Tamano:    5368709120 bytes
SHA-256:   a1b2c3d4e5...
SHA-512:   f6g7h8i9j0...
MD5:       k1l2m3n4o5...
```

### Paso 4: Generar acta de custodia

```bash
forensic_suite acta evidence.raw \
    --perito "Juan Perez" \
    --cedula "V-12345678" \
    --cargo "Perito en Informatica Forense" \
    --caso "MP-2024-001" \
    --json
```

Esto genera `evidence.raw.chain` (Markdown) y `evidence.raw.json` (estructurado).

### Paso 5: Firmar la evidencia

```bash
forensic_suite firmar evidence.raw --key ABC123DEF456
```

Genera `evidence.raw.asc` con la firma GPG detached.

### Paso 6: Obtener sello de tiempo

```bash
# Obtener timestamp
forensic_suite timestamp evidence.raw

# Verificar timestamp
forensic_suite verificar-timestamp evidence.raw.tsr
```

Genera `evidence.raw.tsa.tsr` con el sello RFC 3161 de un TSA publico.

### Paso 7: Generar manifest

```bash
forensic_suite manifest /mnt/forense/ \
    --caso "MP-2024-001" \
    --perito "Juan Perez" \
    -v
```

Genera `manifest.json` con hashes de todos los archivos y verificacion inmediata.

### Paso 8: Desmontar al finalizar

```bash
sudo forensic_suite desbloquear /dev/sdb
```

## Comandos de referencia rapida

| Comando | Que hace |
|---|---|
| `forensic_suite hash <file>` | Hashes SHA-256/SHA-512/MD5 |
| `forensic_suite hash <file> -a sha256` | Solo SHA-256 |
| `forensic_suite hash <file> -g` | Genera archivos .sha256/.sha512/.md5 |
| `forensic_suite verificar <file> <hash>` | Verifica integridad |
| `forensic_suite listar` | Lista discos conectados |
| `forensic_suite bloquear /dev/sdX` | Bloquea escritura (root) |
| `forensic_suite desbloquear /dev/sdX` | Desbloquea |
| `forensic_suite acta <file> --perito X` | Genera acta MP 2017 |
| `forensic_suite firmar <file> --key K` | Firma GPG |
| `forensic_suite timestamp <file>` | Sello RFC 3161 |
| `forensic_suite verificar-timestamp <tsr>` | Verifica sello de tiempo |
| `forensic_suite manifest <dir>` | Genera manifest JSON |
| `forensic_suite verificar-manifest <json>` | Verifica manifest |
| `forensic_suite perito --ver` | Muestra config del perito |
| `forensic_suite daemon status` | Estado del daemon |
