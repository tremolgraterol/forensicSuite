# FORENSIA DIGITAL PARA PRINCIPIANTES
# Paso a Paso desde Cero - Sin Nada a la Imaginacion

**Nivel:** Principiante absoluto
**Prerequisitos:** Ninguno
**Objetivo:** Entender y ejecutar un proceso forense completo

---

## CAPITULO 1: ANTES DE EMPEZAR

### 1.1 Que es esto?

Imagina que eres un detective, pero en vez de buscar huellas dactilares, buscas **datos en computadoras**. La forensia digital es:

```
TOMAR UNA COMPUTADORA → BUSCAR PRUEBAS → PRESENTAR EN TRIBUNAL
```

### 1.2 Por que no puedes simplemente "copiar archivos"?

Porque si haces eso:
- Los archivos se modifican (Windows crea archivos automaticamente)
- El abogado dice: "Usted altero la evidencia"
- Tu caso se pierde

### 1.3 Las 3 reglas de oro

```
REGLA 1: NUNCA tocar la evidencia original
         (siempre trabajar sobre copias)

REGLA 2: NUNCA hacer nada sin documentarlo
         (si no esta escrito, no existio)

REGLA 3: NUNCA perder el control de la evidencia
         (cadena de custodia ininterrumpida)
```

---

## CAPITULO 2: QUE NECESITAS

### 2.1 Equipo fisico que necesitas comprar/conseguir

```
OBLIGATORIO:
├── USB de 32GB o mas ($10)     ← Para bootear Linux forense
├── Disco duro externo 1TB ($50) ← Para guardar clones
├── Adaptador SATA-USB ($15)     ← Para conectar discos internos
├── Guantes de nitrilo ($5)      ← Para no contaminar
├── Cinta de evidencia ($10)     ← Para sellos
├── Camara fotografica ($0)      ← Puede ser tu celular
└── Lapiz y papel ($2)           ← Para notas

OPCIONAL PERO RECOMENDADO:
├── Write-blocker USB ($50-200)  ← Bloqueo hardware
├── Segundo USB de 32GB ($10)    ← Backup
└── Bolso antiestatico ($15)     ← Para transportar evidencia
```

### 2.2 Equipo software que necesitas

```
EN TU COMPUTADORA (la que vas a usar para analizar):
├── Linux (Debian, Ubuntu o CAINE)
├── forensic_suite (ya lo tienes)
└── Internet (para descargar)

EN USB FORENSE (el que vas a bootear):
├── CAINE Linux (descargar de caine-live.net)
└── Herramientas incluidas en CAINE
```

### 2.3 Como preparar el USB forense

**Paso 1: Descargar CAINE**
```
1. Ir a: https://www.caine-live.net/
2. Click en "Download"
3. Elegir "caine_14.0.iso"
4. Esperar a que descargue (2GB aprox)
```

**Paso 2: Crear USB booteable**
```
En Linux:
1. Insertar USB de 32GB
2. Abrir terminal
3. Ejecutar:

sudo dd if=caine_14.0.iso of=/dev/sdX bs=4M status=progress

IMPORTANTE: Reemplazar sdX con tu USB
Para saber cual es: lsblk
(Segun donde diga "USB" o "8GB" o "16GB")
```

**Paso 3: Probar que funciona**
```
1. Insertar USB
2. Reiniciar computadora
3. Entrar a BIOS (F2, F12 o DEL al prender)
4. Seleccionar "Boot from USB"
5. Deberia cargar CAINE Linux
```

---

## CAPITULO 3: EL PROCESO PASO A PASO

### ESCENARIO: Encontraron un USB sospechoso

Imagina: Llegas a una oficina. Hay un USB conectado a una computadora. Dicen que tiene documentos robados.

**Tu mision:** Obtener esos documentos de forma que sea valida en tribunal.

---

### PASO 1: LLEGAR Y DOCUMENTAR (5 minutos)

**Que hacer:**
1. No tocar nada aun
2. Sacar tu camara (celular sirve)
3. Fotografiar TODO

**Que fotografiar:**
```
Foto 1: La habitacion completa (donde esta la computadora)
Foto 2: La computadora de cerca (que tiene conectado)
Foto 3: El USB conectado (que puerto, que marca)
Foto 4: La pantalla (que muestra)
Foto 5: Cualquier numero de serie visible
```

**Escribir en tu cuaderno:**
```
FECHA: 19/07/2026
HORA: 10:30 AM
LUGAR: Oficina 301, Edificio X
QUIEN ME LLAMO: Lic. Martinez
QUE ME DIJO: "Encontraron un USB con documentos robados"
QUE VEO: Computadora Dell, pantalla encendida, USB azul conectado
```

**Con la suite (opcional):**
```bash
# Si tienes tu laptop Linux lista:
forensic_suite listar
# Esto muestra los dispositivos conectados
```

---

### PASO 2: IDENTIFICAR EL DISPOSITIVO (10 minutos)

**Antes de tocar el USB, necesitas saber QUE es.**

**Pregunta al dueño:**
```
"Es este USB?" (señalar el USB)
"De quien es?"
"Cuando se uso por ultima vez?"
"Que contiene?"
```

**Registrar las respuestas:**
```
USB: Kingston DataTraveler 32GB, color azul
Dueno: Empleado Juan Perez
Ultimo uso: Ayer
Dice contiene: "Documentos de contabilidad"
```

**Con la suite:**
```bash
forensic_suite listar
```

**Salida:**
```
DISPOSITIVOS DETECTADOS:
  /dev/sda        Samsung SSD 500GB    476.9 GB    SATA
  /dev/sdb        USB Kingston 32GB    29.8 GB     USB    ← ESTE
```

**Sin la suite:**
```bash
lsblk -o NAME,SIZE,TYPE,MODEL
```

**Salida:**
```
NAME   SIZE TYPE MODEL
sda    500G disk Samsung SSD 860 EVO
sdb     30G disk Kingston DataTraveler 3.0
```

---

### PASO 3: BLOQUEAR ESCRITURA (5 minutos)

**PORQUE:** Si no bloqueas, cuando conectes el USB a tu computadora, ella va a escribir datos (archivos temporales, metadatos, etc). Eso contamina la evidencia.

**COMO funciona el bloqueo:**
```
Tu computadora                     USB
     │                              │
     │  "Quiero escribir datos"     │
     │ ─────────────────────────►   │
     │                              │
     │  "NO, esta bloqueado"        │
     │ ◄─────────────────────────── │
     │                              │
```

**Paso 3.1: Conectar write-blocker (si tienes)**
```
USB del sospechoso → Write-blocker → Tu laptop
```

**Paso 3.2: Bloquear con la suite**
```bash
sudo forensic_suite bloquear /dev/sdb
```

**Salida:**
```
Bloqueando /dev/sdb...
  Verificando bloqueo...
  Dispositivo bloqueado correctamente
```

**Paso 3.3: Verificar que se bloqueo**
```bash
sudo forensic_suite listar
```

**Salida:**
```
DISPOSITIVOS DETECTADOS:
  /dev/sdb        USB Kingston 32GB    29.8 GB     USB    BLOQUEADO
```

**Sin la suite:**
```bash
# Bloquear
sudo blockdev --setro 1 /dev/sdb

# Verificar
sudo blockdev --getro /dev/sdb
# Si dice "1" = bloqueado
# Si dice "0" = no bloqueado
```

**Verificación pasiva:**
```bash
# Confirmar que el bloqueo está activo sin intentar escribir en la evidencia
sudo blockdev --getro /dev/sdb
# Salida: 1 = bloqueado
```

> Nunca escribas sobre la evidencia para comprobar el bloqueo: la verificación debe ser pasiva.

---

### PASO 4: CLONAR EL DISPOSITIVO (15-60 minutos)

**PORQUE:** Nunca trabajas sobre el original. Si algo sale mal, el original esta intacto.

**QUE es un clon:**
```
ORIGINAL (USB)                    CLON (copia exacta)
┌─────────────┐                   ┌─────────────┐
│ Archivo A   │   bit a bit      │ Archivo A   │
│ Archivo B   │ ═══════════════► │ Archivo B   │
│ Archivo C   │   (copia exacta) │ Archivo C   │
│ Eliminado X │                   │ Eliminado X │
└─────────────┘                   └─────────────┘
     32GB                             32GB
```

**Paso 4.1: Crear carpeta para evidencia**
```bash
mkdir -p /evidencia/caso_001
```

**Paso 4.2: Clonar con la suite**
```bash
sudo dcfldd if=/dev/sdb of=/evidencia/caso_001/usb_clona.raw bs=4M hash=sha256
```

**Que significa cada parte:**
```
dcfldd          ← Herramienta de clonado (como dd pero mejor)
if=/dev/sdb     ← Input file (de donde leer)
of=/evidencia/  ← Output file (donde guardar)
bs=4M           ← Block size (tamano de bloque, 4MB es rapido)
hash=sha256     ← Calcular hash mientras clona
```

**Salida:**
```
30712+1 registros escritos
30712+1 registros leidos
128000000 bytes (128 MB, 122 MiB) copiados, 45.234 s, 2.8 MB/s
SHA-256 hash of /dev/sdb:
a1b2c3d4e5f6g7h8i9j0... (hash largo)
```

**Sin la suite:**
```bash
# Con dd (sin hash)
sudo dd if=/dev/sdb of=/evidencia/caso_001/usb_clona.raw bs=4M status=progress

# Con sha256sum despues
sha256sum /evidencia/caso_001/usb_clona.raw
```

**Tiempo estimado:**
- USB 32GB → ~5 minutos (USB 3.0)
- USB 32GB → ~15 minutos (USB 2.0)
- Disco 1TB → ~2 horas (USB 3.0)
- Disco 1TB → ~8 horas (USB 2.0)

---

### PASO 5: CALCULAR HASH (2 minutos)

**PORQUE:** El hash es la "huella digital" del archivo. Si alguien modifica el clon, el hash cambia y lo sabes.

**QUE es un hash:**
```
Archivo original  →  SHA-256 = "a1b2c3..."
Archivo modificado → SHA-256 = "x9y8z7..."

Si los hashes son DIFERENTES → el archivo fue modificado
Si los hashes son IGUALES    → el archivo esta intacto
```

**Paso 5.1: Hash seguro con la suite**
```bash
forensic_suite hash /evidencia/caso_001/usb_clona.raw -g
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
GPG: Firma automatica generada
```

**Sin la suite:**
```bash
# SHA-256
sha256sum /evidencia/caso_001/usb_clona.raw

# SHA-512
sha512sum /evidencia/caso_001/usb_clona.raw

# MD5
md5sum /evidencia/caso_001/usb_clona.raw
```

**GUARDAR EL ARCHIVO .hash** Los necesitas despues para verificacion.

---

### PASO 6: CREAR CADENA DE CUSTODIA (10 minutos)

**PORQUE:** En tribunal necesitas probar:
- Quien recolecto la evidencia
- Cuando la recolecto
- Como la recolecto
- Quien la tuvo en su poder
- Que no fue alterada

**QUE es la cadena de custodia:**
```
DOCUMENTO que registra:
├── Quien (perito, cedula, titulo)
├── Que (descripcion del dispositivo)
├── Cuando (fecha, hora)
├── Donde (lugar)
├── Como (metodo de recoleccion)
├── Hashes (SHA-256, SHA-512, MD5)
├── Transferencias (quien la recibio)
└── Firmas (GPG, timestamp)
```

**Paso 6.1: Generar acta con la suite**
```bash
forensic_suite acta /evidencia/caso_001/usb_clona.raw \
  --perito "Tu Nombre" \
  --cedula "V-12345678" \
  --cargo "Perito Forense Digital" \
  --caso "MP-2024-001" \
  --autoridad "Ministerio Publico"
```

**Salida:**
```
ACTA DE CADENA DE CUSTODIA GENERADA:
  Archivo: usb_clona.raw.acta.json
  Fecha: 2026-07-19T10:45:00
  SHA-256 acta: d1e2f3a4b5c6...
```

**Paso 6.2: Firmar con GPG**
```bash
forensic_suite firmar /evidencia/caso_001/usb_clona.raw
```

**Paso 6.3: Obtener sello de tiempo**
```bash
forensic_suite timestamp /evidencia/caso_001/usb_clona.raw
```

**Sin la suite:**
```bash
# Crear acta manual (JSON)
cat > /evidencia/caso_001/acta.json << EOF
{
  "identificacion": {
    "numero_acta": "001",
    "fecha": "$(date -Iseconds)",
    "lugar": "Oficina 301, Edificio X"
  },
  "colector": {
    "nombre": "Tu Nombre",
    "cedula": "V-12345678",
    "cargo": "Perito Forense Digital",
    "autoridad": "Ministerio Publico"
  },
  "evidencia": {
    "tipo": "USB Kingston 32GB",
    "serial": "ABC123456",
    "descripcion": "Clon bit a bit",
    "hash_sha256": "$(sha256sum usb_clona.raw | cut -d' ' -f1)"
  },
  "metodo": {
    "bloqueo": "blockdev --setro",
    "clonado": "dcfldd bs=4M",
    "verificacion": "SHA-256 + SHA-512 + MD5"
  }
}
EOF

# Firmar
gpg --detach-sign /evidencia/caso_001/acta.json

# Timestamp
openssl ts -query -data /evidencia/caso_001/acta.json -sha256 -out /evidencia/caso_001/acta.tsq
curl -s -H "Content-Type: application/timestamp-query" \
  --data-binary @/evidencia/caso_001/acta.tsq \
  http://timestamp.digicert.com > /evidencia/caso_001/acta.tsr
```

---

### PASO 7: ANALIZAR LA EVIDENCIA (30-120 minutos)

**AHORA SI puedes trabajar.** Pero sobre la COPIA, no el original.

**Paso 7.1: Buscar archivos eliminados (File Carving)**
```bash
forensic_suite carve /evidencia/caso_001/usb_clona.raw \
  -p recuperacion \
  -o /evidencia/caso_001/recuperados \
  -m --caso "MP-2024-001"
```

**Que significa:**
```
carve           ← Recuperar archivos eliminados
-p recuperacion ← Usar perfil con 87 tipos de archivo
-o recuperados  ← Guardar aqui los archivos recuperados
-m              ← Generar manifest de integridad
--caso          ← ID del caso
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

**Paso 7.2: Ver que se recupero**
```bash
ls -la /evidencia/caso_001/recuperados/
```

**Sin la suite:**
```bash
# Editar configuracion de Scalpel
sudo nano /etc/scalpel/scalpel.conf
# Descomentar las lineas que quieres buscar:
#   pdf  y  50000000  %PDF  %EOF
#   docx y  10000000  PK\x03\x04  [Content_Types].xml

# Ejecutar
scalpel /evidencia/caso_001/usb_clona.raw -o /evidencia/caso_001/recuperados/

# Ver resultados
ls /evidencia/caso_001/recuperados/
```

---

### PASO 8: DOCUMENTAR HALLAZGOS (15 minutos)

**Paso 8.1: Generar manifest**
```bash
forensic_suite manifest /evidencia/caso_001/recuperados/ \
  --caso "MP-2024-001" \
  --perito "Tu Nombre"
```

**Paso 8.2: Verificar integridad**
```bash
forensic_suite verificar-manifest /evidencia/caso_001/recuperados/manifest.json
```

**Paso 8.3: Verificar que la evidencia no fue alterada**
```bash
forensic_suite verificar /evidencia/caso_001/usb_clona.raw.hash
```

**Salida:**
```
Verificando: usb_clona.raw
SHA-256: VERIFICADO
SHA-512: VERIFICADO
MD5: VERIFICADO
INTEGRIDAD: CONFIRMADA - Los 3 hashes coinciden
```

---

### PASO 9: PREPARAR PARA TRIBUNAL (20 minutos)

**Que necesitas entregar:**
```
CARPETA DEL CASO
├── usb_clona.raw                    ← Clon de la evidencia
├── usb_clona.raw.hash               ← Hash triple seguro (SHA-256+SHA-512+MD5+timestamp)
├── usb_clona.raw.acta.json          ← Cadena de custodia
├── usb_clona.raw.acta.json.sig      ← Firma GPG
├── usb_clona.raw.acta.json.tsr      ← Sello de tiempo
├── recuperados/                     ← Archivos recuperados
│   ├── recuperados/documento1.docx
│   ├── recuperados/foto1.jpg
│   └── manifest.json
├── informe_pericial.docx            ← Tu informe
└── fotos_escena/                    ← Fotos del lugar
    ├── foto1.jpg
    ├── foto2.jpg
    └── foto3.jpg
```

**Incluir en el informe:**
```
INFORME PERICIAL
═══════════════════════════════════════════════════════

1. DATOS DEL PERITO
   Nombre: Tu Nombre
   Cedula: V-12345678
   Titulo: Perito Forense Digital
   Matricula: 12345

2. DATOS DEL CASO
   Numero: MP-2024-001
   Autoridad: Ministerio Publico
   Fecha de solicitud: 19/07/2026

3. OBJETO DE LA EXPERTICIA
   Analisis de USB Kingston 32GB con presuntos documentos robados

4. METODOLOGIA
   - Bloqueo de escritura: blockdev --setro
   - Clonado bit a bit: dcfldd bs=4M
   - Verificacion de integridad: SHA-256 + SHA-512 + MD5
   - Recuperacion de archivos: Scalpel (file carving)
   - Cadena de custodia: Manual Unico MP 2017
   - Firma electronica: GPG + RFC 3161

5. HALLAZGOS
   - Se recuperaron 15 archivos eliminados
   - 5 documentos Word (.docx)
   - 3 documentos PDF
   - 2 hojas de calculo (.xlsx)
   - 5 fotografias (.jpg)
   - Los documentos contienen informacion financiera de la empresa

6. CONCLUSIONES
   El USB contiene documentos de contabilidad que coinciden
   con los reportados como robados. Los metadatos indican
   que fueron creados el 15/07/2026 y eliminados el 18/07/2026.

7. ANEXOS
   A) Cadena de custodia (acta.json)
   B) Hashes de integridad
   C) Firmas electronicas
   D) Sellos de tiempo
   E) Manifest de archivos recuperados

Firma: _________________________
Fecha: 19/07/2026
```

---

## CAPITULO 4: RESUMEN VISUAL

### El flujo completo en una imagen

```
                    LLEGAS A LA ESCENA
                          │
                          ▼
                 ┌─────────────────┐
                 │ 1. FOTOGRAFIAR  │
                 │    TODO         │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ 2. IDENTIFICAR  │
                 │    DISPOSITIVO  │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ 3. BLOQUEAR     │◄── blockdev --setro
                 │    ESCRITURA    │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ 4. CLONAR       │◄── dcfldd if=/dev/sdb of=clona.raw
                 │    BIT A BIT    │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ 5. HASH         │◄── SHA-256 + SHA-512 + MD5
                 │    VERIFICAR    │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ 6. CADENA       │◄── forensic_suite acta
                 │    CUSTODIA     │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ 7. FIRMAR       │◄── forensic_suite firmar
                 │    + TIMESTAMP  │◄── forensic_suite timestamp
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ 8. TRANSPORTAR  │
                 │    SELADA       │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ 9. ANALIZAR     │◄── forensic_suite carve
                 │    EN LAB       │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ 10. INFORME     │
                 │     PERICIAL    │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ 11. TRIBUNAL    │
                 │     PRESENTAR   │
                 └─────────────────┘
```

---

## CAPITULO 5: ERRORES QUE DEBES EVITAR

### Error 1: "Solo voy a copiar los archivos importantes"
**Mal:** `cp /media/usb/*.* /evidencia/`
**Por que:** Copia solo archivos visibles, no los eliminados
**Bien:** `forensic_suite carve usb.raw -p recuperacion -o recuperados/`

### Error 2: "Primero clono y despues verifico"
**Mal:** Clonar sin haber bloqueado primero
**Por que:** Si no bloqueaste, el clon puede estar contaminado
**Bien:** Siempre bloquear ANTES de clonar

### Error 3: "No necesito documentar, ya me acuerdo"
**Mal:** No hacer acta de custodia
**Por que:** Sin documentacion, no hay evidencia legal
**Bien:** Siempre generar acta con forensic_suite acta

### Error 4: "El hash es muy largo, no lo voy a copiar"
**Mal:** No generar archivo .hash
**Por que:** Sin hash no puedes probar integridad
**Bien:** Usar `forensic_suite hash archivo -g` para generar archivo .hash seguro automaticamente

### Error 5: "Voy a analizar directamente en la computadora del sospechoso"
**Mal:** Instalar herramientas en Windows del sospechoso
**Por que:** Contamina la evidencia
**Bien:** Bootear USB Linux y trabajar desde ahi

---

## CAPITULO 6: PREGUNTAS FRECUENTES

### P: Que hago si el USB no tiene nada visible?
**R:** Los archivos pueden estar eliminados. Usa file carving:
```bash
forensic_suite carve usb.raw -p recuperacion -o recuperados/
```

### P: Que hago si la computadora esta encendida?
**R:** NO apagar primero. Volcado de memoria:
```bash
sudo forensic_suite memoria --adquirir
```

### P: Que hago si el disco esta cifrado?
**R:** Buscar la clave en memoria (si esta encendido) o pedir la clave al sospechoso/juez.

### P: Cuanto tiempo dura todo el proceso?
**R:** Depende del tamano:
- USB 32GB: 1-2 horas
- Disco 500GB: 3-4 horas
- Disco 1TB: 6-8 horas

### P: Necesito ser programador para usar forensic_suite?
**R:** No. Solo necesitas saber abrir terminal y escribir comandos.

---

## CAPITULO 7: CHECKLIST DE LA ESCENA

Imprime esto y llévalo contigo:

```
CHECKLIST - PROCESO FORENSE
═══════════════════════════════════════════════════════

LUGAR: _________________________
FECHA: _________________________
HORA LLEGADA: _________________________

[ ] 1. FOTOGRAFIAR ESCENA
    [ ] Foto habitacion completa
    [ ] Foto computadora
    [ ] Foto dispositivo
    [ ] Foto pantalla
    [ ] Foto numero serie

[ ] 2. IDENTIFICAR
    [ ] Marca dispositivo: _______________
    [ ] Modelo: _______________
    [ ] Serial: _______________
    [ ] Tamano: _______________
    [ ] Estado fisico: _______________
    [ ] Quien entrego: _______________

[ ] 3. BLOQUEAR
    [ ] Write-blocker: SI / NO
    [ ] blockdev --setro ejecutado
    [ ] Verificacion: blockdev --getro = 1

[ ] 4. CLONAR
    [ ] dcfldd ejecutado
    [ ] Tamano del clon: _______________
    [ ] Tiempo: _______________

[ ] 5. HASH SEGURO
    [ ] Archivo .hash generado (SHA-256+SHA-512+MD5)
    [ ] Permisos 444 verificados
    [ ] Firma GPG automatica

[ ] 6. CADENA DE CUSTODIA
    [ ] Acta generada
    [ ] Firma GPG
    [ ] Timestamp

[ ] 7. TRANSPORTE
    [ ] Empaquetado
    [ ] Sellado
    [ ] Firmado

FIRMA DEL RECOLECTOR: _______________
FIRMA DEL TESTIGO: _______________
```

---

**FIN DEL MANUAL**

Si sigues estos pasos exactamente, tu evidencia sera valida en tribunal.
Si te saltas algun paso, un abogado puede desestimar tu testimonio.

**REGLA FINAL:** Cuando tengas duda, documenta. Es mejor sobredocumentar que subdocumentar.
