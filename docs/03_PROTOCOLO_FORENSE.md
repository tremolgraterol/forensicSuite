# 03 - Protocolo Forense

Pasos obligatorios para una extraccion de evidencia digital valida en Venezuela.

## Marco normativo

- COPP Art. 187: Cadena de custodia
- COPP Art. 191: Prueba ilicita = nulidad absoluta
- LECD (G.O. 37.313): Delitos informaticos
- Manual MP 2017: Formato de cadena de custodia
- ISO 27037: Preservar evidencia en estado original

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
