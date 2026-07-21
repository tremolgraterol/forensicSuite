# FORENSIC SUITE - Manual Completo de Uso v2.0.0

## TODO sobre la herramienta

---

## QUE ES FORENSIC SUITE

Es una herramienta que **automatiza** los pasos del proceso forense.
En vez de escribir 10 comandos de Linux, escribes 1 comando de la suite.

```
SIN LA SUITE:                    CON LA SUITE:
                                 
1. blockdev --setro 1 /dev/sdb   forensic_suite bloquear /dev/sdb
2. dcfldd if=... of=...          
3. sha256sum clona.raw           forensic_suite hash clona.raw
4. sha512sum clona.raw           
5. md5sum clona.raw              
6. Crear acta.json manualmente   forensic_suite acta clona.raw --perito "Tu"
7. gpg --detach-sign acta.json   forensic_suite firmar acta.json
8. openssl ts -query ...         forensic_suite timestamp acta.json
9. scalpel clona.raw -o out/     forensic_suite carve clona.raw
10. volatility3 -f mem.raw ...   forensic_suite memoria --analizar --dump mem.raw
```

---

## INSTALACION

### Requisitos
```
- Linux (Debian, Ubuntu, Kali, CAINE)
- Python 3.9 o superior
- root (sudo) para bloquear dispositivos
```

> **Aviso de seguridad (v2.0.0)**: El daemon de bloqueo automatico detecta y excluye el dispositivo desde el cual corre el sistema operativo actual. En un equipo encendido normalmente ese es el disco interno. Si arrancas desde un **USB Live forense**, el USB se considera raíz y el **disco interno del anfitrión sí se puede bloquear** como evidencia. El comando `sudo forensic_suite daemon uninstall` restaura los dispositivos a lectura/escritura.

### Instalar
```bash
# Clonar o copiar la carpeta forensic_suite
cd /home/tu_usuario/Documentos/EST_AN_FORENCE/forensic_suite

# Instalar
sudo ./install.sh

# Verificar que funciona
forensic_suite --version
```

### Si no funciona el comando
```bash
# Opcion 1: Ejecutar directamente
python3 -m forensic_suite --help

# Opcion 2: Agregar al PATH
export PATH="$HOME/.local/bin:$PATH"

# Opcion 3: Crear alias
alias fs='python3 -m forensic_suite'
fs --help
```

---

## TODOS LOS COMANDOS

### VER AYUDA GENERAL
```bash
forensic_suite --help
```

**Salida:**
```
ForensicSuite - Framework de Analisis Forense Digital

Comandos:
  hash                Calcular hashes criptograficos (usar -g para archivo seguro)
  verificar           Verificar hash de un archivo (acepta .hash o valor manual)
  bloquear            Bloquear escritura de dispositivo
  desbloquear         Desbloquear dispositivo
  listar              Listar dispositivos
  acta                Generar acta de custodia
  firmar              Firmar archivo con GPG
  verificar-firma     Verificar firma GPG
  claves              Listar claves GPG
  timestamp           Obtener sello de tiempo
  verificar-timestamp Verificar sello de tiempo
  manifest            Generar manifest JSON
  verificar-manifest  Verificar manifest
  carve               Recuperar archivos eliminados
  analyze             Analizar resultados de scalpel
  memoria             Volcado/analisis de memoria
  perito              Configuracion del perito
  daemon              Daemon de bloqueo automatico
  interact            Modo interactivo tipo framework
```

---

## COMANDO 1: hash

### Que hace
Calcula la "huella digital" de un archivo. Si el archivo cambia aunque sea 1 byte, el hash cambia.
Con `-g` genera archivos individuales `.sha256`, `.sha512`, `.md5` con formato estandar, un archivo `.hash` consolidado con permisos 444, timestamp, y firma GPG automatica si hay clave configurada.

### Cuando usarlo
- Despues de clonar un disco
- Despues de copiar evidencia
- Para verificar que nada fue modificado
- Usar `-g` para generar archivo .hash seguro automaticamente

### Sintaxis
```bash
forensic_suite hash <archivo>
forensic_suite hash <archivo> -a sha256    # Solo SHA-256
forensic_suite hash <archivo> -a sha512    # Solo SHA-512
forensic_suite hash <archivo> -a md5       # Solo MD5
forensic_suite hash <archivo> -g           # Guardar en archivo .hash
```

### Ejemplo completo
```bash
# Calcular todos los hashes y guardar en archivo seguro
forensic_suite hash usb_clona.raw -g
```

**Salida:**
```
Archivo: usb_clona.raw
Tamano: 32212254720 bytes

SHA-256: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2
SHA-512: f1e2d3c4b5a6f7e8d9c0b1a2f3e4d5c6b7a8f9e0d1c2b3a4f5e6d7c8b9a0f1e2d3c4b5a6f7e8d9c0b1a2
MD5:     1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d

Hash guardado en: usb_clona.raw.hash
Permisos: 444 (solo lectura)
GPG: Firma automatica generada (si GPG disponible)
```

### Contenido del archivo .hash seguro
```
# usb_clona.raw.hash - Secure Hash File
# Generado: 2026-07-19T10:45:00-04:00
# Permisos: 444 (read-only)
SHA-256: a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2
SHA-512: f1e2d3c4b5a6f7e8d9c0b1a2f3e4d5c6b7a8f9e0d1c2b3a4f5e6d7c8b9a0f1e2d3c4b5a6f7e8d9c0b1a2
MD5: 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d
FILENAME: usb_clona.raw
TIMESTAMP: 2026-07-19T10:45:00-04:00
```

### Guardar hash en archivo
```bash
forensic_suite hash usb_clona.raw -g
# Crea: usb_clona.raw.hash
```

**Contenido del archivo .hash:**
```
SHA-256: a1b2c3d4e5f6...
SHA-512: f1e2d3c4b5a6...
MD5:     1a2b3c4d5e6f...
```

### Sin la suite
```bash
# SHA-256
sha256sum usb_clona.raw

# SHA-512
sha512sum usb_clona.raw

# MD5
md5sum usb_clona.raw

# No genera archivo .hash seguro automaticamente
# No establece permisos 444 automaticamente
# No genera firma GPG automaticamente
```

---

## COMANDO 2: verificar

### Que hace
Verifica que un archivo no fue modificado comparando su hash con uno conocido.
Acepta archivos .hash generados con `-g` (verifica SHA-256+SHA-512+MD5 automaticamente) o valores de hash manuales.

### Cuando usarlo
- Despues de hashear evidencia con `-g`
- Antes de analizar evidencia
- Para confirmar que el clon es identico al original
- Para detectar manipulacion

### Sintaxis
```bash
forensic_suite verificar <archivo.hash>
forensic_suite verificar <archivo> <hash_sha256>    # Verificacion manual legacy
```

### Ejemplo completo (método recomendado)
```bash
# Generar hash seguro primero
forensic_suite hash usb_clona.raw -g

# Verificar automaticamente (compara los 3 hashes)
forensic_suite verificar usb_clona.raw.hash
```

**Salida (integro):**
```
Verificando: usb_clona.raw
SHA-256: a1b2c3d4... (esperado)
SHA-256: a1b2c3d4... (actual)
SHA-512: f1e2d3c4... (esperado)
SHA-512: f1e2d3c4... (actual)
MD5: 1a2b3c4d... (esperado)
MD5: 1a2b3c4d... (actual)

INTEGRIDAD: VERIFICADA
Los 3 hashes coinciden. El archivo NO fue modificado.
```

**Salida (alterado):**
```
Verificando: usb_clona.raw
SHA-256: a1b2c3d4... (esperado)
SHA-256: x9y8z7w6... (actual)

INTEGRIDAD: COMPROMETIDA
El archivo FUE MODIFICADO.
```

### Sin la suite
```bash
# Calcular hash actual
sha256sum usb_clona.raw

# Comparar con el hash original manualmente
# Si son diferentes, el archivo fue modificado

# Limitaciones del metodo manual:
# - Solo verifica SHA-256, no SHA-512 ni MD5
# - No genera archivo .hash seguro
# - No establece permisos 444
# - No genera firma GPG automatica
```

---

## COMANDO 3: bloquear

### Que hace
Impide que se escriban datos en un dispositivo. Esto protege la evidencia de ser contaminada.

### Cuando usarlo
**SIEMPRE** antes de tocar un dispositivo de evidencia.

### Sintaxis
```bash
sudo forensic_suite bloquear <dispositivo>
```

### Ejemplo completo
```bash
sudo forensic_suite bloquear /dev/sdb
```

**Salida:**
```
Bloqueando /dev/sdb...
  Verificando bloqueo...
  Dispositivo bloqueado correctamente
```

### Verificar que se bloqueo
```bash
forensic_suite listar
```

**Salida:**
```
DISPOSITIVOS DETECTADOS:
  /dev/sda        Samsung SSD 500GB    476.9 GB    SATA
  /dev/sdb        USB Kingston 32GB    29.8 GB     USB    BLOQUEADO
```

### Sin la suite
```bash
# Bloquear
sudo blockdev --setro 1 /dev/sdb

# Verificar
sudo blockdev --getro /dev/sdb
# 1 = bloqueado
# 0 = no bloqueado

# Probar que funciona
sudo touch /dev/sdb
# Deberia decir: Read-only file system
```

---

## COMANDO 4: desbloquear

### Que hace
Remueve el bloqueo de escritura. Solo para cuando terminaste de trabajar.

### Sintaxis
```bash
sudo forensic_suite desbloquear <dispositivo>
```

### Ejemplo
```bash
sudo forensic_suite desbloquear /dev/sdb
```

### Sin la suite
```bash
sudo blockdev --setro 0 /dev/sdb
```

---

## COMANDO 5: listar

### Que hace
Muestra todos los dispositivos de almacenamiento conectados (discos duros, USB, etc).

### Sintaxis
```bash
forensic_suite listar
```

### Ejemplo
```bash
forensic_suite listar
```

**Salida:**
```
DISPOSITIVOS DETECTADOS:
  /dev/sda        Samsung SSD 500GB    476.9 GB    SATA
  /dev/sdb        USB Kingston 32GB    29.8 GB     USB    BLOQUEADO
  /dev/sdc        Transcend 16GB       14.9 GB     USB
```

### Sin la suite
```bash
lsblk -o NAME,SIZE,TYPE,MODEL
```

**Salida:**
```
NAME   SIZE TYPE MODEL
sda    500G disk Samsung SSD 860 EVO
sdb     30G disk Kingston DataTraveler 3.0
sdc     15G disk Transcend JetFlash
```

---

## COMANDO 6: acta

### Que hace
Genera el documento de cadena de custodia (requerido por ley).

### Cuando usarlo
Despues de clonar y hashear la evidencia.

### Sintaxis
```bash
forensic_suite acta <archivo_evidencia> \
  --perito "Nombre" \
  --cedula "V-12345678" \
  --cargo "Perito Forense" \
  --caso "MP-2024-001" \
  --autoridad "Ministerio Publico"
```

### Ejemplo completo
```bash
forensic_suite acta usb_clona.raw \
  --perito "Juan Perez" \
  --cedula "V-12345678" \
  --cargo "Perito Forense Digital" \
  --caso "MP-2024-001" \
  --autoridad "Ministerio Publico" \
  --json
```

**Salida:**
```
ACTA DE CADENA DE CUSTODIA GENERADA:
  Archivo: usb_clona.raw.acta.json
  Fecha: 2026-07-19T10:45:00
  SHA-256 acta: d1e2f3a4b5c6...
```

**Contenido del JSON:**
```json
{
  "identificacion": {
    "numero_acta": "001",
    "fecha": "2026-07-19T10:45:00-04:00",
    "lugar": "Laboratorio de Forensia"
  },
  "colector": {
    "nombre": "Juan Perez",
    "cedula": "V-12345678",
    "cargo": "Perito Forense Digital",
    "autoridad": "Ministerio Publico"
  },
  "evidencia": {
    "tipo": "Archivo raw",
    "nombre": "usb_clona.raw",
    "hash_sha256": "a1b2c3d4...",
    "hash_sha512": "f1e2d3c4...",
    "hash_md5": "1a2b3c4d..."
  }
}
```

### Sin la suite
```bash
cat > acta.json << EOF
{
  "identificacion": {
    "numero_acta": "001",
    "fecha": "$(date -Iseconds)"
  },
  "colector": {
    "nombre": "Juan Perez",
    "cedula": "V-12345678"
  },
  "evidencia": {
    "hash_sha256": "$(sha256sum usb_clona.raw | cut -d' ' -f1)"
  }
}
EOF
```

---

## COMANDO 7: firmar

### Que hace
Firma un archivo con tu clave GPG. Esto prueba que TU creaste ese archivo y que no fue modificado.

### Sintaxis
```bash
forensic_suite firmar <archivo>
```

### Ejemplo
```bash
forensic_suite firmar usb_clona.raw.acta.json
```

**Salida:**
```
Firmando: usb_clona.raw.acta.json
Firma generada: usb_clona.raw.acta.json.sig
```

### Verificar firma
```bash
forensic_suite verificar-firma usb_clona.raw.acta.json --firma usb_clona.raw.acta.json.asc
```

**Salida:**
```
Firma: VALIDA
Firmante: Juan Perez <juan@email.com>
Fecha: 2026-07-19
```

### Sin la suite
```bash
# Firmar
gpg --detach-sign usb_clona.raw.acta.json

# Verificar
gpg --verify usb_clona.raw.acta.json.sig usb_clona.raw.acta.json
```

---

## COMANDO 8: timestamp

### Que hace
Obtiene un sello de tiempo de una autoridad internacional. Esto prueba que el archivo existia en esa fecha.

### Sintaxis
```bash
# Obtener timestamp
forensic_suite timestamp <archivo>

# Verificar timestamp
forensic_suite verificar-timestamp <archivo.tsr>
```

### Ejemplo
```bash
# Obtener
forensic_suite timestamp usb_clona.raw.acta.json

# Verificar
forensic_suite verificar-timestamp usb_clona.raw.acta.json.tsr
```

**Salida:**
```
Timestamp RFC 3161 obtenido
  TSA:       http://timestamp.digicert.com
  Fecha:     2026-07-20T17:30:05.937109+00:00
  Hash:      600a400ad2cccbc84aa81bc02fafbae9a051cab703b19c3737d0b86820ee5a40
  Token:     /home/user/forense_practica/clones/doc.txt.tsr
```

### Sin la suite
```bash
# Crear solicitud
openssl ts -query -digest <hash_hex> -no_nonce -cert > acta.tsq

# Enviar a TSA
curl -s -H "Content-Type: application/timestamp-query" \
  --data-binary @acta.tsq \
  http://timestamp.digicert.com > acta.tsr

# Verificar
openssl ts -reply -in acta.tsr -text
```

---

## COMANDO 9: manifest

### Que hace
Crea un archivo JSON con los hashes de TODOS los archivos en un directorio.

### Sintaxis
```bash
forensic_suite manifest <directorio> --caso "MP-2024-001" --perito "Juan"
```

### Ejemplo
```bash
forensic_suite manifest /evidencia/recuperados/ --caso "MP-2024-001"
```

**Salida:**
```
Manifest generado: /evidencia/recuperados/manifest.json
Archivos incluidos: 15
SHA-256 manifest: d4e5f6a7b8c9...
```

**Contenido del manifest:**
```json
{
  "caso": "MP-2024-001",
  "fecha": "2026-07-19T11:00:00",
  "total_archivos": 15,
  "tamano_total": 23456789,
  "archivos": [
    {
      "nombre": "documento1.docx",
      "ruta": "recuperados/documento1.docx",
      "tamano": 45678,
      "sha256": "a1b2c3d4...",
      "sha512": "f1e2d3c4...",
      "md5": "1a2b3c4d..."
    }
  ]
}
```

### Verificar manifest
```bash
forensic_suite verificar-manifest /evidencia/recuperados/manifest.json
```

---

## COMANDO 10: carve

### Que hace
Recupera archivos eliminados de un disco o imagen. Busca patrones de inicio/fin de archivos.

### Sintaxis
```bash
forensic_suite carve <fuente> -p <perfil> -o <salida>
```

### Perfiles disponibles
```bash
forensic_suite carve --perfiles
```

**Salida:**
```
PERFILES DISPONIBLES:
Perfil          Tipos    Descripcion
---------------------------------------------------------------------------
recuperacion    87       Archivos eliminados, particiones, datos residuales
cripto          63       Claves privadas, certificados, tokens, credenciales
medios          70       Fotos, videos, audio, evidencia multimedia
documentos      49       Ofimatica, textos, correos, formularios
redes           35       Capturas de red, logs, firewall, PCAP
general         39       Configuracion general, 39 tipos comunes
```

### Ejemplo: Recuperar todo
```bash
forensic_suite carve usb_clona.raw -p recuperacion -o recuperados
```

**Salida:**
```
Fuente: usb_clona.raw
Salida: recuperados/
Ejecutando scalpel...

  ARCHIVOS RECUPERADOS: 15
  Tamano total: 23456789 bytes
  Tiempo: 45.2s

  POR TIPO:
    .docx      5 archivo(s)
    .pdf       3 archivo(s)
    .xlsx      2 archivo(s)
    .jpg       5 archivo(s)
```

### Ejemplo: Recuperar solo claves
```bash
forensic_suite carve usb_clona.raw -p cripto -o claves
```

### Ejemplo: Con manifest
```bash
forensic_suite carve usb_clona.raw -p recuperacion -o recuperados \
  -m --caso "MP-2024-001" --perito "Juan"
```

### Ejemplo: Ver tipos configurados
```bash
forensic_suite carve usb_clona.raw --listar-tipos
```

### Sin la suite
```bash
# Editar configuracion
sudo nano /etc/scalpel/scalpel.conf

# Ejecutar
scalpel usb_clona.raw -o recuperados/
```

---

## COMANDO 11: memoria

### Que hace
Adquiere y analiza memoria RAM (volatil).

### Sintaxis
```bash
forensic_suite memoria --adquirir
forensic_suite memoria --analizar --dump <archivo>
forensic_suite memoria --verificar --dump <archivo>
forensic_suite memoria --verificar-entorno
```

### Verificar entorno
```bash
forensic_suite memoria --verificar-entorno
```

**Salida:**
```
ENTORNO DE MEMORIA FORENSE
========================================
mforense:    OK
Root:        NO (requiere sudo)
LiME:        NO DISPONIBLE
AVML:        DISPONIBLE
Volatility:  DISPONIBLE
```

### Adquirir memoria
```bash
sudo forensic_suite memoria --adquirir
```

**Salida:**
```
ADQUIRIENDO MEMORIA VOLATIL...
Esto puede tardar varios minutos dependiendo de la RAM
[Progreso: 100%]
Dump generado: memoria.raw
SHA-256: a1b2c3d4...
```

### Analizar memoria
```bash
forensic_suite memoria --analizar --dump memoria.raw --plugin windows.pslist
```

**Salida:**
```
PID     Process Name        PPID    Threads  Creates
------  ------------------  ------  -------  -------------------
4       System              0       116      2026-07-19 08:00:00
132     smss.exe            4       3        2026-07-19 08:00:00
256     csrss.exe           132     12       2026-07-19 08:00:01
...
```

### Plugins populares
```bash
# Lista de procesos
forensic_suite memoria --analizar --dump mem.raw --plugin windows.pslist

# Conexiones de red
forensic_suite memoria --analizar --dump mem.raw --plugin windows.netscan

# Archivos abiertos
forensic_suite memoria --analizar --dump mem.raw --plugin windows.filescan

# DLLs cargadas
forensic_suite memoria --analizar --dump mem.raw --plugin windows.dlllist
```

### Sin la suite
```bash
# Adquirir
sudo avml /tmp/memoria.raw

# Analizar
volatility3 -f memoria.raw windows.pslist
volatility3 -f memoria.raw windows.netscan
```

---

## COMANDO 12: perito

### Que hace
Configura los datos del perito (nombre, cedula, clave GPG).

### Sintaxis
```bash
forensic_suite perito --configurar
forensic_suite perito --ver
forensic_suite perito --info
```

### Configurar
```bash
forensic_suite perito --configurar
```

**Pide:**
```
Nombre: Juan Perez
Cedula: V-12345678
Cargo: Perito Forense Digital
Clave GPG: juan@email.com
```

### Ver configuracion
```bash
forensic_suite perito --ver
```

### Info del sistema
```bash
forensic_suite perito --info
```

---

## COMANDO 13: daemon

### Que hace
Instala un servicio que bloquea automaticamente los USB cuando se conectan.

### Sintaxis
```bash
sudo forensic_suite daemon install
sudo forensic_suite daemon status
sudo forensic_suite daemon uninstall
```

### Instalar
```bash
sudo forensic_suite daemon install
```

**Salida:**
```
Daemon instalado correctamente
Servicio: forensic-blockerd.service
Regla udev: 10-forensic-block.rules
Reiniciando udev...
```

### Ver estado
```bash
sudo forensic_suite daemon status
```

**Salida:**
```
ESTADO DEL SISTEMA FORENSE
========================================
Servicio:       ACTIVO
Regla udev:     INSTALADA
Bloqueo:        blockdev --setro (configurado)
```

### Desinstalar
```bash
sudo forensic_suite daemon uninstall
```

---

## EJEMPLOS COMBINADOS

### Ejemplo 1: USB completo (desde cero)
```bash
# 1. Listar dispositivos
forensic_suite listar

# 2. Bloquear
sudo forensic_suite bloquear /dev/sdb

# 3. Clonar
sudo dcfldd if=/dev/sdb of=/evidencia/usb.raw bs=4M hash=sha256

# 4. Hash seguro
forensic_suite hash /evidencia/usb.raw -g

# 5. Cadena de custodia
forensic_suite acta /evidencia/usb.raw --perito "Juan" --caso "X"

# 6. Firmar
forensic_suite firmar /evidencia/usb.raw.acta.json

# 7. Timestamp
forensic_suite timestamp /evidencia/usb.raw.acta.json

# 8. Recuperar archivos
forensic_suite carve /evidencia/usb.raw -p recuperacion -o /evidencia/recuperados

# 9. Manifest
forensic_suite manifest /evidencia/recuperados/ --caso "X"

# 10. Verificar todo
forensic_suite verificar /evidencia/usb.raw.hash
```

### Ejemplo 2: Servidor encendido
```bash
# 1. NO APAGAR - Primero memoria
sudo forensic_suite memoria --adquirir

# 2. Documentar procesos
ps aux > /evidencia/procesos.txt

# 3. Bloquear disco
sudo forensic_suite bloquear /dev/sda

# 4. Clonar disco
sudo dcfldd if=/dev/sda of=/evidencia/disco.raw bs=4M

# 5. Apagar
sudo shutdown -h now

# 6. Analizar memoria
forensic_suite memoria --analizar --dump /evidencia/memoria.raw

# 7. Analizar disco
forensic_suite carve /evidencia/disco.raw -p general -o /evidencia/recuperados
```

---

## ERRORES COMUNES Y SOLUCIONES

### Error: "permission denied" en bloquear
**Causa:** No estas ejecutando como root
**Solucion:**
```bash
sudo forensic_suite bloquear /dev/sdb
```

### Error: "device not found" en listar
**Causa:** El dispositivo no esta conectado o no lo ves
**Solucion:**
```bash
# Verificar con lsblk
lsblk

# Si no aparece, reconectar el USB
```

### Error: "scalpel no encontrado" en carve
**Causa:** Scalpel no esta instalado
**Solucion:**
```bash
sudo apt install scalpel
```

### Error: "gpg no encontrado" en firmar
**Causa:** GPG no esta instalado o no tienes clave
**Solucion:**
```bash
# Instalar
sudo apt install gnupg

# Generar clave
gpg --full-generate-key
```

### Error: "avml no encontrado" en memoria
**Causa:** AVML no esta instalado
**Solucion:**
```bash
sudo curl -L -o /usr/local/bin/avml \
  https://github.com/microsoft/avml/releases/download/v0.18.0/avml
sudo chmod +x /usr/local/bin/avml
```

---

## AUDITORIA FORENSE (Integridad)

ForensicSuite v2.0.0 implementa una auditoría inmutable de comandos en modo interactivo:

1.  **Registro:** Cada comando ejecutado en `forensic >` se registra automáticamente en `auditoria_<CASO>.log`.
2.  **Integridad:** Cada registro es firmado criptográficamente con la clave GPG del perito configurado (`.log.asc`).
3.  **Transparencia:** Esto permite a un contra-perito verificar que las acciones realizadas por el perito no han sido alteradas durante el análisis.

---

## RESUMEN RAPIDO

| Que necesitas | Comando |
|---------------|---------|
| Ver dispositivos | `forensic_suite listar` |
| Bloquear disco | `sudo forensic_suite bloquear /dev/sdX` |
| Hash seguro | `forensic_suite hash archivo -g` |
| Verificar integridad | `forensic_suite verificar archivo.hash` |
| Crear acta | `forensic_suite acta archivo --perito "Nombre"` |
| Firmar | `forensic_suite firmar archivo` |
| Timestamp | `forensic_suite timestamp archivo` |
| Verificar timestamp | `forensic_suite verificar-timestamp archivo.tsr` |
| Recuperar archivos | `forensic_suite carve archivo -p perfil -o salida` |
| Analizar memoria | `forensic_suite memoria --analizar --dump mem.raw` |
| Verificar entorno | `forensic_suite memoria --verificar-entorno` |
| Configurar perito | `forensic_suite perito --configurar` |
| Instalar daemon | `sudo forensic_suite daemon install` |

**REGLA:** Siempre empieza con `forensic_suite listar` para ver que hay conectado.
**REGLA:** Usa `-g` al hashear para generar archivos .hash seguros automaticamente.

---

## ANEXO: Clase 11 - Carving Avanzado

Para profundizar en **Scalpel, Foremost, Bulk Extractor, expresiones regulares y busqueda de cadenas**, consulta el documento:

```
forensic_suite/docs/CLASE_11_CARVING_AVANZADO.md
```

Incluye:
- Diferencias entre Foremost, Scalpel y Bulk Extractor.
- Sintaxis de reglas de Scalpel y ejemplos de perfiles.
- Uso de `strings` + `grep` con expresiones regulares.
- Casos de uso recomendados por tipo de investigacion.
- Ejercicios practicos en `forensic_suite/docs/EJERCICIOS_PRACTICOS_2.md`.

Nuevo perfil disponible:

```bash
forensic_suite carve evidencia.raw -p mensajeria -o ./recuperados -m
```

---

**FIN DEL MANUAL**
