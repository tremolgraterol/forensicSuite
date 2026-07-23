# 03 - Protocolo Forense

Pasos obligatorios para una extraccion de evidencia digital valida en Venezuela.

## Marco normativo

- COPP Art. 187: Cadena de custodia
- COPP Art. 191: Prueba ilicita = nulidad absoluta
- LECD (G.O. 37.313): Delitos informaticos
- Manual MP 2017: Formato de cadena de custodia
- ISO 27037: Identificar, recolectar, adquirir y preservar evidencia digital
- NIST SP 800-86: Integrar técnicas forenses en la respuesta a incidentes
- RFC 3227: Priorizar la recolección conforme al orden de volatilidad

## Fase 0: Preparacion (antes del contacto)

1. Verificar que la herramienta este instalada y funcional:
```bash
forensic_suite --version
forensic_suite perito --ver
```

2. Verificar entorno del sistema:
```bash
forensic_suite perito --info
```

3. Verificar que GPG y OpenSSL estan disponibles:
```bash
gpg --version
openssl version
```

## Caso especial: evidencia en memoria de un sistema encendido

La RAM solo existe mientras el equipo está encendido. Por ello, la adquisición se realiza **en el mismo equipo bajo examen**, no en una estación separada. Usar un segundo equipo es recomendable como estación de análisis, para preparar medios verificados y para conservar copias, pero no permite capturar la RAM del equipo objetivo.

### Principio del observador

Todo contacto con un sistema vivo lo modifica: ejecutar comandos, cargar LiME o AVML, escribir el dump y calcular hashes consume CPU, memoria y puede modificar registros, cachés, procesos, temporales y logs. Esta alteración es inevitable para preservar la evidencia volátil y **no debe ocultarse ni describirse como una adquisición sin cambios**.

La justificación debe registrarse: la pérdida de la RAM al apagar o esperar supera la alteración controlada, mínima y reproducible producida por la adquisición. El perito debe emplear la herramienta previamente verificada, ejecutar la menor cantidad de acciones necesaria, conservar su hash/versión y dejar trazabilidad completa.

### Secuencia documentada para RAM viva

1. Obtener autorización y asignar identificador de caso.
2. Registrar fecha/hora, zona horaria, identidad del operador, estado visible del equipo, conexiones, sesiones y medios conectados.
3. Fotografiar o video-documentar la escena cuando corresponda.
4. Verificar previamente el hash, versión y procedencia del recolector en un medio confiable.
5. Ejecutar la fijación mínima necesaria del estado vivo (procesos, red, usuarios, módulos y hora), anotando cada comando y su hora.
6. Adquirir la RAM en el mismo equipo mediante LiME/AVML; registrar herramienta, versión, parámetros, ruta destino, inicio, finalización, errores y alteraciones observadas.
7. Calcular hashes del dump terminado, crear el acta/cadena de custodia y conservar el original sin analizarlo.
8. Transferir el dump y su documentación a una estación de análisis; verificar hashes antes de trabajar únicamente sobre una copia.
9. Solo después, según el caso, preservar/clonar el almacenamiento persistente o apagar el equipo.

Este procedimiento aplica los principios de identificación, recolección, adquisición y preservación de ISO 27037. La validez no depende de una inexistente “no alteración”, sino de que la alteración necesaria esté justificada, minimizada, registrada y sea verificable.

## Fase 1: Bloqueo (NIVEL 0 - Critico)

**REGLA**: El dispositivo DEBE estar bloqueado ANTES de que el SO lo toque.

```bash
# 1. Identificar el dispositivo
forensic_suite listar

# 2. Bloquear (requiere root)
sudo forensic_suite bloquear /dev/sdX
```

El bloqueo ejecuta en orden:
1. `hdparm -r1 /dev/sdX` → firmware
2. `blockdev --setro /dev/sdX` → kernel block layer
3. `losetup --read-only --find --show /dev/sdX` → loop device
4. `mount -o ro,loop,noexec,noosuid,nodev,noatime` → montaje

**Verificar** que el bloqueo esta activo:
```bash
hdparm -r /dev/sdX | grep "readonly"
blockdev --getro /dev/sdX
mount | grep sdX
```

## Fase 2: Adquisicion de hashes

```bash
# Calcular hashes del dispositivo completo o archivo de evidencia
forensic_suite hash /mnt/forense/evidence.raw
```

Los hashes se calculan:
- SHA-256 (64 chars hex) - estandar ISO 27037
- SHA-512 (128 chars hex) - seguridad extendida
- MD5 (32 chars hex) - redundancia

**Registrar** los 3 hashes en el acta de custodia.

## Fase 3: Generar acta de custodia

```bash
forensic_suite acta /mnt/forense/evidence.raw \
    --perito "Nombre del Perito" \
    --cedula "V-12.345.678" \
    --cargo "Perito en Informatica Forense" \
    --caso "MP-2024-001" \
    --json
```

Esto genera:
- `evidence.raw.chain` → Acta en Markdown (6 secciones MP 2017)
- `evidence.raw.json` → Acta en JSON estructurado

## Fase 4: Firma digital

```bash
forensic_suite firmar evidence.raw --key ID_CLAVE_GPG
```

Genera `evidence.raw.asc` con firma GPG detached.

La firma:
- Prueba QUIEN firmo
- Se invalida si el archivo se modifica

**Nota legal**: GPG no es PSC acreditado por SUSCERTE. Para uso judicial, considerar certificado de PSC acreditado.

## Fase 5: Sello de tiempo

```bash
forensic_suite timestamp evidence.raw
```

Genera `evidence.raw.tsa.tsr` con sello RFC 3161.

El sello provee:
- Fecha exacta de cuando existia ese hash
- Firma del servidor TSA (DigiCert/Sectigo/Entrust)
- Prueba de que el archivo existia en ese momento exacto

## Fase 6: Manifest de integridad

```bash
forensic_suite manifest /ruta/evidencia/ \
    --caso "MP-2024-001" \
    --perito "Nombre del Perito" \
    -v
```

Genera `manifest.json` con:
- Hashes de cada archivo (SHA-256/SHA-512/MD5)
- Hash del propio manifest (SHA-256 + SHA-512)
- Verificacion inmediata con `-v`

## Fase 7: Verificacion

```bash
# Verificar un archivo individual
forensic_suite verificar evidence.raw <sha256_esperado>

# Verificar manifest completo
forensic_suite verificar-manifest /ruta/manifest.json
```

## Fase 8: Desmontaje

Al finalizar todas las operaciones:

```bash
sudo forensic_suite desbloquear /dev/sdX
```

## Checklist de custodia

| # | Paso | Obligatorio | Herramienta |
|---|---|---|---|
| 1 | Configurar perito | Si | `perito --configurar` |
| 2 | Bloquear dispositivo | Si | `bloquear /dev/sdX` |
| 3 | Calcular hashes | Si | `hash <archivo>` |
| 4 | Generar acta MP 2017 | Si | `acta <archivo>` |
| 5 | Firmar con GPG | Recomendado | `firmar <archivo>` |
| 6 | Sello de tiempo | Recomendado | `timestamp <archivo>` |
| 7 | Generar manifest | Si | `manifest <dir>` |
| 8 | Verificar todo | Si | `verificar` + `verificar-manifest` |
| 9 | Desmontar | Si | `desbloquear /dev/sdX` |

## Errores comunes que invalidan evidencia

1. **No bloquear antes del montaje**: Si el SO escribio algo, la evidencia esta comprometida
2. **No registrar hashes en el acta**: Sin hashes no hay prueba de integridad
3. **No generar acta**: Sin acta no hay cadena de custodia valida
4. **Usar solo MD5**: MD5 tiene colisiones conocidas, usar SHA-256 como minimo
5. **No verificar despues de generar**: Los hashes pueden fallar si hay error de disco
