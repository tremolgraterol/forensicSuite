# GUIA COMPLETA: Proceso Forense Digital
# From Zero to Expert - Teoria, Protocolo y Practica

**Autor:** Tr3w01
**Version:** 1.0.0
**Marco Legal:** Venezuela (G.O. 37.313), ISO 27037, NIST SP 800-86, RFC 3227

---

## INDICE

1. [Fundamentos Teoricos](#1-fundamentos-teoricos)
2. [Marco Legal](#2-marco-legal)
3. [Protocolo Forense Completo](#3-protocolo-forense-completo)
4. [Fase 0: Preparacion](#4-fase-0-preparacion)
5. [Fase 1: Identificacion](#5-fase-1-identificacion)
6. [Fase 2: Preservacion (Bloqueo)](#6-fase-2-preservacion-bloqueo)
7. [Fase 3: Adquisicion](#7-fase-3-adquisicion)
8. [Fase 4: Analisis](#8-fase-4-analisis)
9. [Fase 5: Documentacion y Presentacion](#9-fase-5-documentacion-y-presentacion)
10. [Escenarios Reales](#10-escenarios-reales)
11. [Errores Comunes y Como Evitarlos](#11-errores-comunes-y-como-evitarlos)
12. [Referencias](#12-referencias)

---

## 1. FUNDAMENTOS TEORICOS

### 1.1 Que es la Forensia Digital?

La forensia digital es la aplicacion de metodos cientificos para:
- **Identificar** evidencia digital
- **Preservar** su integridad
- **Analizar** su contenido
- **Presentar** hallazgos en tribunal

### 1.2 Por que es importante?

La evidencia digital es **frágil**. A diferencia de una huella dactilar (que no cambia), los datos digitales:
- Se modifican con cada operacion del sistema
- Se pueden borrar automaticamente
- Se degradan con el tiempo
- Se pueden alterar sin querer

**Ejemplo:** Si conectas un USB a una computadora Windows:
- Windows crea archivos `Thumbs.db` (thumbnails)
- Windows actualiza el registro de ultima conexion
- El antivirus puede modificar metadatos
- Todo esto **contamina** la evidencia

### 1.3 Principios Fundamentales

| Principio | Significado | Consecuencia |
|-----------|-------------|--------------|
| **No alterar** | Nunca modificar la evidencia original | Siempre trabajar sobre copias |
| **Documentar** | Registrar cada accion | Si no esta documentado, no existio |
| **Cadena de custodia** | Trazabilidad de quien toco que | Sin custodia, no hay evidencia |
| **Reproducibilidad** | Otro perito debe poder repetir el proceso | Metodos estandarizados |

---

## 2. MARCO LEGAL

### 2.1 Leyes Aplicables (Venezuela)

| Ley | Articulo | Relevancia |
|-----|----------|------------|
| **LECD** (G.O. 37.313) | Art. 1-14 | Delitos informaticos, penas, definiciones |
| **COPP** | Art. 183 | cadena de custodia de evidencia |
| **COPP** | Art. 187 | Acta de cadena de custodia |
| **COPP** | Art. 191 | Perito experto |
| **COPP** | Art. 224-225 | Dictamen pericial |
| **Ley Mensajes de Datos** | Art. 6 | Firma electronica |

### 2.2 Jurisprudencia Clave

| Sentencia | Fecha | Criterio |
|-----------|-------|----------|
| TSJ C25-49 | 28/05/2025 | La evidencia digital sigue el Manual Unico de Custodia |
| TSJ Sala Social N523 | 12/11/2024 | Solo la Experticia Informatica es valida |
| TSJ Sala Civil N769 | 24/10/2007 | El juez no sustituye al perito |

### 2.3 Estandares Internacionales

| Estandar | Organismo | Aplicacion |
|----------|-----------|------------|
| ISO 27037 | ISO | Identificacion, recoleccion, preservacion |
| NIST SP 800-86 | NIST | Tecnicas forenses |
| RFC 3227 | IETF | Orden de volatilidad en recoleccion |

---

## 3. PROTOCOLO FORENSE COMPLETO

### 3.1 El Orden Correcto (RFC 3227)

```
                    VOLATILIDAD (mas a menos)
                    ┌─────────────────────────┐
                    │ 1. Memoria RAM           │ ← Se pierde al apagar
                    │ 2. Estado del sistema    │ ← Procesos, conexiones
                    │ 3. Temporales del OS     │ ← Se borran solos
                    │ 4. Disco duro            │ ← Persiste
                    │ 5. Logs impresos         │ ← Ya no cambian
                    └─────────────────────────┘
```

### 3.2 Flujo Completo

```
┌─────────────────────────────────────────────────────────────┐
│                    ESCENA DEL CRIMEN                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. PREPARACION                                             │
│     ├── Verificar jurisdiccion                              │
│     ├── Obtener orden judicial (si aplica)                  │
│     ├── Preparar equipo (herramientas, medios)              │
│     └── Documentar fecha/hora de llegada                    │
│                                                             │
│  2. IDENTIFICACION                                          │
│     ├── Seguridad del lugar                                 │
│     ├── Fotografiar escena                                  │
│     ├── Identificar dispositivos                            │
│     └── Documentar estado inicial                           │
│                                                             │
│  3. PRESERVACION (BLOQUEO)                                  │
│     ├── Bloquear escritura de dispositivos                  │
│     ├── No apagar sistemas encendidos                       │
│     └── Proteger contra interferencias                      │
│                                                             │
│  4. ADQUISICION                                             │
│     ├── Volcado de memoria RAM (si esta encendido)          │
│     ├── Clonado bit a bit de discos                        │
│     ├── Hashing de evidencia original                       │
│     └── Documentar todo en cadena de custodia               │
│                                                             │
│  5. TRANSPORTE                                              │
│     ├── Empaquetar evidencia                                │
│     ├── Sellar con cinta de evidencia                       │
│     ├── Firmar sellos                                       │
│     └── Registrar transferencia                             │
│                                                             │
│  6. ANALISIS (en laboratorio)                               │
│     ├── Trabajar SOLO sobre copias                          │
│     ├── Recuperar archivos eliminados                       │
│     ├── Analizar memoria (si hay dump)                      │
│     ├── Extraer metadatos                                   │
│     └── Correlacionar hallazgos                             │
│                                                             │
│  7. DOCUMENTACION                                           │
│     ├── Generar informe pericial                            │
│     ├── Incluir hash de integridad                          │
│     ├── Firmar con GPG                                      │
│     ├── Obtener sello de tiempo                             │
│     └── Presentar en tribunal                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. FASE 0: PREPARACION

### 4.1 Que necesitas antes de ir a la escena

**Equipo fisico:**
- Laptop con Linux (Debian/Ubuntu)
- Discos duros externos (para clones)
- USB booteables con herramientas
- Cintas de evidencia (para sellos)
- Camara fotografica
- Guantes de nitrilo
- Bolsas antiestaticas

**Equipo software:**
- forensic_suite (nuestra herramienta)
- Volatility (analisis de memoria)
- LiME/AVML (adquisicion de memoria)
- Scalpel/Foremost (file carving)
- Sleuth Kit (analisis de filesystems)

### 4.2 Verificar jurisdiccion

**Antes de actuar, pregunta:**
1. Tienes autoridad para actuar?
2. Necesitas orden judicial?
3. Que leyes aplican en este territorio?
4. Quien es la autoridad competente?

**En Venezuela:**
- Delitos informaticos: MP (Ministerio Publico)
- COPP Art. 183: cadena de custodia
- Ley Especial contra Delitos Informaticos: G.O. 37.313

---

## 5. FASE 1: IDENTIFICACION

### 5.1 Que es identificar?

Documentar **que** esta presente en la escena **antes** de tocar nada.

### 5.2 Que documentar

| Elemento | Que registrar | Ejemplo |
|----------|---------------|---------|
| **Dispositivo** | Marca, modelo, serie | "Samsung SSD 860 EVO, Serie S3Z9NS0K123456" |
| ** Conexion** | Tipo, puerto | "USB 3.0, puerto frontal" |
| **Tamano** | Capacidad | "500 GB" |
| **Estado fisico** | Danos, etiquetas | "Sin danos visibles, etiqueta de evidencia #001" |
| **Estado logico** | Encendido/apagado | "Encendido, pantalla activa" |
| **Entorno** | Red, perifericos | "Conectado a LAN, mouse USB" |

### 5.3 Ejemplo practico con la suite

**Con forensic_suite:**
```bash
# Listar dispositivos conectados
forensic_suite listar
```

**Salida esperada:**
```
DISPOSITIVOS DETECTADOS:
  /dev/sda        Intel SSD 512GB    476.9 GB    SATA
  /dev/sdc        USB Disk 16GB      14.9 GB     USB
```

**Sin la suite (manual):**
```bash
# Listar discos
lsblk -o NAME,SIZE,TYPE,MODEL

# Ver información detallada
sudo hdparm -I /dev/sda

# Para USB
lsusb
```

### 5.4 Por que importa?

Si no identificas el dispositivo **antes** de tocarlo:
- No puedes probar en tribunal que es el mismo disco
- No puedes vincular la evidencia al caso
- Un abogado puede argumentar que cambiaste el dispositivo

---

## 6. FASE 2: PRESERVACION (BLOQUEO)

### 6.1 Que es el bloqueo de escritura?

Impedir que el sistema operativo o el hardware modifiquen la evidencia.

### 6.2 Por que es critico?

Sin bloqueo:
```
Tu conectas USB → Windows escribe "Thumbs.db"
→ Eso modifica el disco
→ El hash cambia
→ La evidencia esta contaminada
→ El abogado dice: "Usted altero la evidencia"
→ Tu caso se cae
```

### 6.3 Las 4 capas de bloqueo

```
┌─────────────────────────────────────────────────────────┐
│ CAPA 4: mount -o ro                                     │
│   └── Le dice al filesystem: "solo lectura"             │
│                                                         │
│ CAPA 3: losetup --ro                                   │
│   └── Le dice al emulador de dispositivo: "solo lectura"│
│                                                         │
│ CAPA 2: blockdev --setro                               │
│   └── Le dice al kernel: "no escribas a este disco"    │
│                                                         │
│ CAPA 1: hdparm -r1                                     │
│   └── Le dice al firmware del disco: "bloquea escritura"│
└─────────────────────────────────────────────────────────┘
```

### 6.4 Cual capa usar cuando?

| Dispositivo | hdparm | blockdev | Reason |
|-------------|--------|----------|--------|
| **Disco SATA interno** | SI | SI | hdparm funciona con ATA |
| **USB** | NO | SI | USB no entiende comandos ATA |
| **NVMe** | NO | SI | NVMe usa protocolo distinto |
| **RAID** | Dependiendo | SI | blockdev es universal |

**Regla de oro:** Siempre usar `blockdev` como minimo. `hdparm` es complementario.

### 6.5 Ejemplo practico

**Con forensic_suite:**
```bash
# Bloquear USB (usa blockdev automaticamente)
sudo forensic_suite bloquear /dev/sdc

# Salida:
# Bloqueando /dev/sdc...
# Verificando bloqueo...
# Dispositivo bloqueado correctamente
```

**Sin la suite (manual):**
```bash
# Paso 1: firmware (solo SATA)
sudo hdparm -r1 /dev/sdc
# Para USB: "ioctl HDIO_SET_READONLY failed: No such device or address"

# Paso 2: kernel (funciona para todos)
sudo blockdev --setro 1 /dev/sdc

# Verificar
sudo blockdev --getro /dev/sdc
# 1 = bloqueado, 0 = desbloqueado
```

### 6.6 Verificar que el bloqueo funciona

**Con forensic_suite:**
```bash
# La suite verifica automaticamente
sudo forensic_suite bloquear /dev/sdc
# Incluye verificacion post-bloqueo
```

**Sin la suite (manual):**
```bash
# Verificar que esta bloqueado
sudo blockdev --getro /dev/sdc
# Salida: 1

# Intentar escribir (deberia fallar)
sudo touch /dev/sdc
# touch: cannot touch '/dev/sdc': Read-only file system
```

### 6.7 Sistema en caliente (computadora encendida)

**NO bloquear directamente.** Primero:

```bash
# 1. Documentar estado
ps aux > procesos.txt
netstat -tulpn > conexiones.txt

# 2. Volcado de memoria (URGENTE)
sudo mforense acquire
# o
sudo avml /tmp/memoria.avml

# 3. DESPUES bloquear disco
sudo blockdev --setro 1 /dev/sda

# 4. Clonar
sudo dcfldd if=/dev/sda of=/backup/clona.raw bs=4M
```

### 6.8 Que pasa si no bloqueas?

| Escenario | Consecuencia | Legal |
|-----------|--------------|-------|
| USB a Windows | Windows escribe metadatos | Evidencia contaminada |
| Servidor Linux | Logs se actualizan | Datos alterados |
| Computadora encendida | Procesos escriben | Cache modificado |

---

## 7. FASE 3: ADQUISICION

### 7.1 Que es adquisicion?

Crear una **copia exacta** bit a bit del dispositivo original.

### 7.2 Tipos de adquisicion

| Tipo | Metodo | Cuando usar |
|------|--------|-------------|
| **Bit a bit** | `dd`, `dcfldd` | Evidencia principal |
| **Logico** | `tar`, `cp` | Archivos especificos |
| **Memoria** | `LiME`, `AVML` | RAM volatil |
| **Red** | `tcpdump`, `wireshark` | Captura de paquetes |

### 7.3 Clonado bit a bit

**Con forensic_suite:**
```bash
# Listar dispositivos para elegir
forensic_suite listar

# Clonar (usar dcfldd para progreso)
sudo dcfldd if=/dev/sdc of=/evidencia/usb_clona.raw bs=4M hash=sha256
```

**Sin la suite (manual):**
```bash
# Con dd (sin progreso)
sudo dd if=/dev/sdc of=/evidencia/usb_clona.raw bs=4M status=progress

# Con dcfldd (con hash integrado)
sudo dcfldd if=/dev/sdc of=/evidencia/usb_clona.raw bs=4M hash=sha256

# Verificar tamano
ls -lh /evidencia/usb_clona.raw
```

### 7.4 Volcado de memoria RAM

**Con forensic_suite:**
```bash
# Verificar entorno
forensic_suite memoria --verificar-entorno

# Adquirir memoria
sudo forensic_suite memoria --adquirir
```

**Sin la suite (manual):**
```bash
# Con LiME
sudo insmod lime.ko "path=/tmp/memoria.lime format=lime"

# Con AVML
sudo avml /tmp/memoria.avml

# Verificar
ls -lh /tmp/memoria.*
```

### 7.5 Hashing de evidencia

**Con forensic_suite:**
```bash
# Hash triple seguro (SHA-256 + SHA-512 + MD5 + timestamp + filename)
forensic_suite hash usb_clona.raw -g

# Salida:
# Archivo: usb_clona.raw
# Tamano: 16106127360 bytes
# SHA-256: a1b2c3d4e5f6...
# SHA-512: f6e5d4c3b2a1...
# MD5: 1234567890abcdef...
# Hash guardado en: usb_clona.raw.hash
# Permisos: 444 (solo lectura)
# GPG: Firma automatica generada (si GPG disponible)
```

**Sin la suite (manual):**
```bash
# SHA-256
sha256sum usb_clona.raw

# SHA-512
sha512sum usb_clona.raw

# MD5
md5sum usb_clona.raw
```

### 7.6 Por que hash triple?

- **SHA-256**: Estandar NIST, usado en tribunales
- **SHA-512**: Mayor seguridad, misma familia SHA-2
- **MD5**: Rapido, para comparacion (no recomendado solo)

Si un hash cambia, la evidencia fue alterada.

### 7.7 Cadena de custodia

**Con forensic_suite:**
```bash
# Generar acta MP 2017
forensic_suite acta usb_clona.raw \
  --perito "Juan Perez" \
  --cedula "V-12345678" \
  --cargo "Perito Forense" \
  --caso "MP-2024-001" \
  --autoridad "Ministerio Publico"

# Firmar con GPG
forensic_suite firmar usb_clona.raw.acta.json

# Sello de tiempo
forensic_suite timestamp usb_clona.raw.acta.json
```

**Sin la suite (manual):**
```bash
# Crear acta manualmente (JSON)
cat > acta.json << EOF
{
  "identificacion": {
    "fecha": "$(date -Iseconds)",
    "lugar": "Laboratorio de Forensia",
    "caso": "MP-2024-001"
  },
  "colector": {
    "nombre": "Juan Perez",
    "cedula": "V-12345678",
    "cargo": "Perito Forense"
  },
  "evidencia": {
    "descripcion": "Clon USB",
    "hash_sha256": "$(sha256sum usb_clona.raw | cut -d' ' -f1)"
  }
}
EOF

# Firmar
gpg --detach-sign acta.json

# Timestamp (RFC 3161)
openssl ts -query -data acta.json -sha256 -out acta.tsq
curl -s -H "Content-Type: application/timestamp-query" \
  --data-binary @acta.tsq \
  http://timestamp.digicert.com > acta.tsr
```

---

## 8. FASE 4: ANALISIS

### 8.1 Principio fundamental

**NUNCA trabajar sobre la evidencia original.** Siempre sobre la copia.

### 8.2 Tipos de analisis

| Tipo | Herramienta | Que busca |
|------|-------------|-----------|
| **File carving** | Scalpel, Foremost | Archivos eliminados |
| **Analisis de memoria** | Volatility | Procesos, conexiones, malware |
| **Metadatos** | ExifTool, TSK | Fechas, autores, GPS |
| **Cifrado** | John, Hashcat | Contraseñas |
| **Red** | Wireshark, NetworkMiner | Trafico capturado |

### 8.3 File carving (Recuperar archivos eliminados)

**Con forensic_suite:**
```bash
# Ver perfiles disponibles
forensic_suite carve --perfiles

# Recuperar con perfil general
forensic_suite carve usb_clona.raw -p recuperacion -o recuperados

# Recuperar solo cripto (claves, certificados)
forensic_suite carve usb_clona.raw -p cripto -o cripto_recuperado

# Con manifest de integridad
forensic_suite carve usb_clona.raw -p medios -o fotos -m --caso "MP-2024-001"
```

**Sin la suite (manual):**
```bash
# Editar configuracion de Scalpel
sudo nano /etc/scalpel/scalpel.conf
# Descomentar las lineas de los tipos que buscas

# Ejecutar
scalpel usb_clona.raw -o recuperados/

# Ver resultados
ls recuperados/
```

### 8.4 Analisis de memoria

**Con forensic_suite:**
```bash
# Verificar entorno
forensic_suite memoria --verificar-entorno

# Analizar dump con plugin especifico
forensic_suite memoria --analizar \
  --dump memoria.raw \
  --plugin windows.pslist

# Verificar integridad
forensic_suite memoria --verificar --dump memoria.raw
```

**Sin la suite (manual):**
```bash
# Con Volatility
volatility3 -f memoria.raw windows.pslist
volatility3 -f memoria.raw windows.netscan
volatility3 -f内存.raw windows.filescan

# Plugins populares
volatility3 -f memoria.raw windows.pstree
volatility3 -f memoria.raw windows.dlllist
volatility3 -f memoria.raw windows.handlelist
```

### 8.5 Perfiles de carving explicados

| Perfil | Tipos | Ejemplos | Cuandousar |
|--------|-------|----------|------------|
| **recuperacion** | 87 | jpg, pdf, zip, exe, sqlite | Evidencia general |
| **cripto** | 63 | pem, key, ssh, gpg, shadow | Acceso no autorizado |
| **medios** | 70 | jpg, mp4, mp3, avi, raw | Fotos/videos |
| **documentos** | 49 | docx, pdf, xlsx, odt, eml | Documentos oficina |
| **redes** | 35 | pcap, log, conf, pem | Analisis de red |
| **general** | 39 | Los 39 tipos mas comunes | Uso diario |

---

## 9. FASE 5: DOCUMENTACION Y PRESENTACION

### 9.1 Que incluir en el informe pericial

```
INFORME PERICIAL
├── Datos del perito (nombre, cedula, titulo)
├── Datos del caso (numero, autoridad, fecha)
├── Objeto de la experticia
├── Metodologia utilizada
├── Herramientas empleadas
├── Resultados del analisis
├── Hallazgos relevantes
├── Conclusiones
├── Anexos
│   ├── Cadena de custodia
│   ├── Hashes de integridad
│   ├── Firmas GPG
│   └── Sellos de tiempo
└── Firma del perito
```

### 9.2 Generar documentacion con la suite

```bash
# 1. Generar hash seguro (genera archivo .hash con permisos 444)
forensic_suite hash /evidencia/usb_clona.raw -g

# 2. Generar manifest de todos los archivos
forensic_suite manifest /evidencia/ --caso "MP-2024-001" --perito "Juan Perez"

# 3. Verificar manifest
forensic_suite verificar-manifest /evidencia/manifest.json

# 4. Verificar integridad automaticamente (compara los 3 hashes)
forensic_suite verificar /evidencia/usb_clona.raw.hash

# 5. Obtener sello de tiempo
forensic_suite timestamp /evidencia/usb_clona.raw
```

### 9.3 Sin la suite

```bash
# Manifest manual
find /evidencia/ -type f -exec sha256sum {} \; > manifest.txt

# Firmar
gpg --detach-sign /evidencia/usb_clona.raw

# Timestamp
openssl ts -query -data /evidencia/usb_clona.raw -sha256 -out evidencia.tsq
```

---

## 10. ESCENARIOS REALES

### 10.1 Escenario: USB con archivos eliminados

**Situacion:** Un sospechoso borró archivos de un USB.

**Proceso:**
```bash
# 1. Identificar
forensic_suite listar
# /dev/sdc USB 16GB

# 2. Bloquear
sudo forensic_suite bloquear /dev/sdc

# 3. Clonar
sudo dcfldd if=/dev/sdc of=/evidencia/usb.raw bs=4M

# 4. Hash seguro
forensic_suite hash /evidencia/usb.raw -g
# Genera: usb.raw.hash (SHA-256 + SHA-512 + MD5 + timestamp + filename)
# Permisos: 444 (solo lectura)
# GPG: Firma automatica generada

# 5. Verificar integridad
forensic_suite verificar /evidencia/usb.raw.hash

# 6. Cadena de custodia
forensic_suite acta /evidencia/usb.raw --perito "Tu" --caso "X"

# 7. Recuperar archivos
forensic_suite carve /evidencia/usb.raw -p recuperacion -o /evidencia/recuperados

# 8. Verificar que se recupero
ls /evidencia/recuperados/
```

### 10.2 Escenario: Servidor encendido

**Situacion:** Un servidor fue atacado y sigue encendido.

**Proceso:**
```bash
# 1. NO APAGAR (primero volcado de memoria)
sudo forensic_suite memoria --adquirir

# 2. Documentar procesos activos
ps aux > /evidencia/procesos.txt
netstat -tulpn > /evidencia/red.txt

# 3. AHORA si bloquear
sudo forensic_suite bloquear /dev/sda

# 4. Clonar
sudo dcfldd if=/dev/sda of=/evidencia/disco.raw bs=4M

# 5. Apagar
sudo shutdown -h now

# 6. Analizar memoria
forensic_suite memoria --analizar --dump /evidencia/memoria.raw

# 7. Analizar disco
forensic_suite carve /evidencia/disco.raw -p general -o /evidencia/recuperados
```

### 10.3 Escenario: Dispositivo cifrado

**Situacion:** Un disco esta cifrado con BitLocker/LUKS.

**Proceso:**
```bash
# 1. Verificar si esta cifrado
sudo cryptsetup isLuks /dev/sda1 && echo "LUKS detectado"

# 2. Si esta encendido, buscar clave en memoria
sudo forensic_suite memoria --adquirir
forensic_suite memoria --analizar --dump memoria.raw --plugin windows.bitlocker

# 3. Si tienes la clave
sudo cryptsetup open /dev/sda1 evidencia
# Ahora puedes acceder a /dev/mapper/evidencia

# 4. Clonar DESPUES de descifrar
sudo dcfldd if=/dev/mapper/evidencia of=/evidencia/descifrado.raw bs=4M
```

---

## 11. ERRORES COMUNES Y COMO EVITARLOS

### 11.1 Errores Fatales

| Error | Consecuencia | Como evitar |
|-------|--------------|-------------|
| No bloquear | Evidencia contaminada | Siempre bloquear primero |
| Trabajar sobre original | Alteracion irreversible | Siempre clonar |
| No documentar | Sin cadena de custodia | Documentar cada paso |
| No hashear | No se puede verificar integridad | Hash despues de cada operacion |
| Apagar sin volcar RAM | Perdida de evidencia volatil | Primero memoria, despues apagar |

### 11.2 Errores Legales

| Error | Consecuencia | Como evitar |
|-------|--------------|-------------|
| Sin orden judicial | Evidencia inadmissible | Verificar jurisdiccion |
| Sin perito habilitado | Dictamen invalido | Verificar credenciales |
| Sin cadena de custodia | Sin evidencia | Usar acta MP 2017 |
| Sin firma electronica | Sin validez legal | Usar GPG + timestamp |

### 11.3 Errores Tecnicos

| Error | Consecuencia | Como evitar |
|-------|--------------|-------------|
| Hash con md5sum solo | Vulnerable a colisiones | Usar SHA-256 minimo |
| Clonar con dd sin bs | Muy lento | Usar bs=4M o mas |
| No verificar bloqueo | Asumir sin confirmar | Verificar con `blockdev --getro` |
| Usar root sin necesidad | Riesgo de accidente |最小权限 principle |

---

## 12. REFERENCIAS

### Estandares
- ISO 27037:2012 - Guidelines for identification, collection, acquisition and preservation of digital evidence
- NIST SP 800-86 - Guide to Integrating Forensic Techniques into Incident Response
- RFC 3227 - Guidelines for Evidence Collection and Archiving

### Leyes (Venezuela)
- Ley Especial contra Delitos Informaticos (G.O. 37.313)
- Codigo Orgánico Procesal Penal (COPP)
- Ley sobre Mensajes de Datos y Firmas Electronicas

### Herramientas
- forensic_suite: Nuestro framework
- mforense: Adquisicion de memoria
- Scalpel: File carving
- Volatility3: Analisis de memoria
- Sleuth Kit: Analisis de filesystems

---

**FIN DE LA GUIA**

Esta documentacion es parte del proceso de peritaje forense digital.
Cualquier uso debe seguir el protocolo y marco legal aplicable.
