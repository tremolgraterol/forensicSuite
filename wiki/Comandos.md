# Comandos de ForensicSuite

## Uso general

```bash
forensic_suite <comando> [opciones]
```

Atajo: `fs` (en Linux si se instaló con `install.sh`).

## Comandos comunes

### Hash y verificación

```bash
# Calcular todos los hashes
forensic_suite hash evidencia.raw

# Solo SHA-256
forensic_suite hash evidencia.raw -a sha256

# Verificar hash
forensic_suite verificar evidencia.raw HASH_HEX
```

### Cadena de custodia

```bash
# Generar acta
forensic_suite acta evidencia.raw --perito "Nombre del perito"

# Generar manifiesto
forensic_suite manifest /ruta/evidencia/ -o manifest.json

# Verificar manifiesto
forensic_suite verificar-manifest manifest.json
```

### Firma y sellos de tiempo

```bash
# Firmar con GPG
forensic_suite firmar evidencia.raw --key ID_CLAVE

# Verificar firma
forensic_suite verificar-firma evidencia.raw.asc

# Sello de tiempo RFC 3161
forensic_suite timestamp evidencia.raw
forensic_suite verificar-timestamp evidencia.raw.tsr
```

### Carving

```bash
# Recuperar archivos con perfil predeterminado
forensic_suite carve imagen.dd -o recuperados/

# Perfil específico (mensajería, imágenes, documentos)
forensic_suite carve imagen.dd -p mensajeria -o recuperados/

# Listar perfiles disponibles
forensic_suite carve --listar-perfiles
```

### Memoria RAM

```bash
# Linux: adquirir
forensic_suite memoria --adquirir --salida memoria.lime

# Analizar con Volatility3
forensic_suite memoria --analizar --dump memoria.raw -p windows.pslist
forensic_suite memoria --analizar --dump memoria.raw -p windows.pstree
forensic_suite memoria --analizar --dump memoria.raw -p windows.netscan
forensic_suite memoria --analizar --dump memoria.raw -p windows.malfind
```

### Dispositivos (Linux)

```bash
# Listar dispositivos
forensic_suite listar

# Bloquear escritura
sudo forensic_suite bloquear /dev/sdb

# Desbloquear
sudo forensic_suite desbloquear /dev/sdb
```

### Modo interactivo

```bash
forensic_suite interact --caso MP-001 --perito "Perito"
```

## Ayuda por comando

```bash
forensic_suite <comando> --help
```

Ejemplo:

```bash
forensic_suite memoria --help
```

## Documentación detallada

Ver [`docs/MANUAL_FORENSIC_SUITE.md`](https://github.com/tremolgraterol/forensicSuite/blob/main/docs/MANUAL_FORENSIC_SUITE.md).
