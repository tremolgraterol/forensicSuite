# EJERCICIOS PRACTICOS - PARTE 2

## EJERCICIO 5: CADENA DE CUSTODIA (15 min)

**Objetivo:** Documentar evidencia correctamente

### Paso 1: Generar acta CON la suite
```bash
forensic_suite acta ~/forense_practica/clones/usb.raw \
  --perito "Estudiante" \
  --cedula "V-99999999" \
  --caso "PRACTICA-001" \
  --json
```

### Paso 2: Ver el acta
```bash
cat ~/forense_practica/clones/usb.raw.acta.json
```
**Identifica:** Tu nombre, el hash, la fecha

### Paso 3: Generar acta SIN la suite
```bash
cat > ~/forense_practica/acta_manual.json << 'EOF'
{
  "identificacion": {
    "numero": "001",
    "fecha": "FECHA_AQUI"
  },
  "colector": {
    "nombre": "Tu Nombre",
    "cedula": "Tu Cedula"
  },
  "evidencia": {
    "hash": "HASH_AQUI"
  }
}
EOF

# Reemplazar hash
sed -i "s/HASH_AQUI/$(sha256sum ~/forense_practica/clones/usb.raw | cut -d' ' -f1)/" ~/forense_practica/acta_manual.json

cat ~/forense_practica/acta_manual.json
```

---

## EJERCICIO 6: FIRMA GPG (15 min)

**Objetivo:** Firmar evidencia digitalmente

### Paso 1: Verificar claves
```bash
forensic_suite claves
```
**Tienes claves?** SI / NO

### Paso 2: Generar clave (si no tienes)
```bash
gpg --full-generate-key
# Tipo: RSA (1)
# Tamano: 4096
# Nombre: Tu Nombre
# Email: tu@email.com
```

### Paso 3: Firmar CON la suite
```bash
forensic_suite firmar ~/forense_practica/clones/usb.raw.acta.json
```

### Paso 4: Verificar firma
```bash
forensic_suite verificar-firma ~/forense_practica/clones/usb.raw.acta.json
```
**Resultado:** VALIDA / INVALIDA

### Paso 5: Firmar SIN la suite
```bash
gpg --detach-sign ~/forense_practica/clones/usb.raw.acta.json
gpg --verify ~/forense_practica/clones/usb.raw.acta.json.sig \
           ~/forense_practica/clones/usb.raw.acta.json
```
**Resultado:** Good signature / BAD signature

---

## EJERCICIO 7: FILE CARVING (45 min)

**Objetivo:** Recuperar archivos eliminados

### Paso 1: Crear archivos para borrar
```bash
sudo umount /dev/sdX 2>/dev/null

echo "Informe confidencial" > /tmp/importante.txt
echo "Datos: 123,456" > /tmp/finanzas.csv
echo "Clave: abc123" > /tmp/credenciales.txt
```

### Paso 2: Copiar al USB
```bash
sudo mount /dev/sdX1 /mnt/usb 2>/dev/null || sudo mount /dev/sdX /mnt/usb
sudo cp /tmp/importante.txt /mnt/usb/
sudo cp /tmp/finanzas.csv /mnt/usb/
sudo mkdir -p /mnt/usb/oculto
sudo cp /tmp/credenciales.txt /mnt/usb/oculto/
ls -la /mnt/usb/
sudo umount /mnt/usb
```

### Paso 3: Borrar archivos
```bash
sudo rm /mnt/usb/importante.txt
sudo rm /mnt/usb/finanzas.csv
sudo rm -rf /mnt/usb/oculto
ls -la /mnt/usb/
```
**Los ves?** SI / NO (correcto)

### Paso 4: Clonar USB borrado
```bash
sudo forensic_suite bloquear /dev/sdX
sudo dcfldd if=/dev/sdX of=~/forense_practica/clones/usb_borrado.raw bs=4M
```

### Paso 5: Recuperar CON la suite
```bash
forensic_suite carve ~/forense_practica/clones/usb_borrado.raw \
  -p recuperacion \
  -o ~/forense_practica/recuperados \
  -m
```
**Cuantos archivos recupero?** ___

### Paso 6: Verificar
```bash
ls -la ~/forense_practica/recuperados/
```
**Ves los archivos borrados?** SI / NO

### Paso 7: Recuperar SIN la suite
```bash
# Editar configuracion de Scalpel
sudo nano /etc/scalpel/scalpel.conf
# Descomentar estas lineas:
#   txt  n  100000  \xff\xfe
#   csv  y  100000  \xff\xfe\x00\x00

# Ejecutar
scalpel ~/forense_practica/clones/usb_borrado.raw -o ~/forense_practica/recuperados_manual/
ls ~/forense_practica/recuperados_manual/
```
**Cuantos recupero manualmente?** ___

---

## EJERCICIO 8: ANALISIS DE MEMORIA (30 min)

**Objetivo:** Analizar dump de memoria RAM

### Paso 1: Verificar entorno
```bash
forensic_suite memoria --verificar-entorno
```
**AVML disponible?** SI / NO
**Volatility disponible?** SI / NO

### Paso 2: Verificar dump existente
```bash
ls -lh /home/tremolgraterol/Documentos/EST_AN_FORENCE/lab_memoria/*.raw
```
**Cual es el mas reciente?** _______________

### Paso 3: Analizar CON la suite
```bash
forensic_suite memoria --analizar \
  --dump /home/tremolgraterol/Documentos/EST_AN_FORENCE/lab_memoria/memoria.raw \
  --plugin windows.pslist
```
**Cuantos procesos aparecen?** ___

### Paso 4: Analizar SIN la suite
```bash
volatility3 -f /home/tremolgraterol/Documentos/EST_AN_FORENCE/lab_memoria/memoria.raw \
  windows.pslist
```
**Los resultados son iguales?** SI / NO

### Paso 5: Buscar conexiones de red
```bash
forensic_suite memoria --analizar \
  --dump /home/tremolgraterol/Documentos/EST_AN_FORENCE/lab_memoria/memoria.raw \
  --plugin windows.netscan
```
**Hay conexiones activas?** SI / NO

---

## EJERCICIO 9: ESCENARIO COMPLETO (60 min)

**Objetivo:** Ejecutar el proceso forense completo

### ESCENARIO
Un empleado renuncio. sospechan que robo documentos en un USB.

### Paso 1: Llegar y documentar
```bash
# En tu cuaderno:
# Fecha: _______________
# Hora: _______________
# Lugar: _______________
# Testigo: _______________

# Fotografiar (usar celular)
# Foto 1: La oficina
# Foto 2: El USB conectado
# Foto 3: La pantalla
```

### Paso 2: Identificar
```bash
forensic_suite listar
```
**USB encontrado:** /dev/___ Tamano: ___ GB

### Paso 3: Bloquear
```bash
sudo forensic_suite bloquear /dev/sdX
sudo blockdev --getro /dev/sdX
```
**Bloqueado:** SI / NO

### Paso 4: Clonar
```bash
sudo dcfldd if=/dev/sdX of=~/forense_practica/CASO_001/usb.raw bs=4M hash=sha256
```
**Hash:** _______________

### Paso 5: Cadena de custodia
```bash
forensic_suite acta ~/forense_practica/CASO_001/usb.raw \
  --perito "Tu Nombre" \
  --cedula "Tu Cedula" \
  --caso "CASO-001" \
  --json
```

### Paso 6: Firmar
```bash
forensic_suite firmar ~/forense_practica/CASO_001/usb.raw.acta.json
```

### Paso 7: Timestamp
```bash
# Obtener timestamp
forensic_suite timestamp ~/forense_practica/CASO_001/usb.raw.acta.json

# Verificar timestamp
forensic_suite verificar-timestamp ~/forense_practica/CASO_001/usb.raw.acta.json.tsr
```

### Paso 8: Recuperar archivos
```bash
forensic_suite carve ~/forense_practica/CASO_001/usb.raw \
  -p recuperacion \
  -o ~/forense_practica/CASO_001/recuperados \
  -m
```
**Archivos recuperados:** ___

### Paso 9: Verificar integridad
```bash
forensic_suite verificar ~/forense_practica/CASO_001/usb.raw.hash
```
**Integridad:** VERIFICADA / COMPROMETIDA

### Paso 10: Documentar hallazgos
```bash
# Crear informe simple
cat > ~/forense_practica/CASO_001/informe.txt << EOF
INFORME PERICIAL
Fecha: $(date)
Caso: CASO-001
Perito: Tu Nombre

HALLAZGOS:
- Se recupero[N] archivos eliminados
- Los archivos contienen: [describir]

CONCLUSION:
[Que encontraste]
EOF
```

---

## EJERCICIO 10: DESAFIO (30 min)

**Objetivo:** Encontrar archivos ocultos

### Preparacion
```bash
# Tu profesor crea un USB con archivos ocultos
# Tu debes encontrarlos

# El USB esta en /dev/sdX
# No sabes que hay adentro
```

### Tu mision
```bash
# 1. Bloquear
sudo forensic_suite bloquear /dev/sdX

# 2. Clonar
sudo dcfldd if=/dev/sdX of=/tmp/desafio.raw bs=4M

# 3. Probar diferentes perfiles
forensic_suite carve /tmp/desafio.raw -p recuperacion -o /tmp/d1
forensic_suite carve /tmp/desafio.raw -p cripto -o /tmp/d2
forensic_suite carve /tmp/desafio.raw -p medios -o /tmp/d3
forensic_suite carve /tmp/desafio.raw -p documentos -o /tmp/d4

# 4. Contar archivos recuperados
ls /tmp/d1/ | wc -l
ls /tmp/d2/ | wc -l
ls /tmp/d3/ | wc -l
ls /tmp/d4/ | wc -l

# 5. Encontrar el archivo mas importante
# Pista: mira los nombres, tamanos, fechas
```

**Cuantos archivos encontro con cada perfil?**
- recuperacion: ___
- cripto: ___
- medios: ___
- documentos: ___

---

## EJERCICIO 11: CARVING AVANZADO CON SCALPEL (Clase 11)

**Objetivo:** Crear un perfil personalizado de Scalpel y recuperar archivos especificos.

### Paso 1: Revisar perfiles disponibles
```bash
forensic_suite carve --perfiles
```

### Paso 2: Usar el perfil de mensajeria
```bash
forensic_suite carve /ruta/a/evidencia.raw \
  -p mensajeria \
  -o ~/forense_practica/clase11_mensajeria \
  -m
```

### Paso 3: Verificar resultados
```bash
ls -R ~/forense_practica/clase11_mensajeria/
cat ~/forense_practica/clase11_mensajeria/carving_manifest.json
```

**Preguntas:**
- ¿Cuantos tipos de archivo configura el perfil `mensajeria`?
- ¿Encontro bases de datos SQLite? ¿Puede abrirlas con `sqlitebrowser`?
- ¿Que extensiones de imagenes recupero?

---

## EJERCICIO 12: COMPARATIVA FOREMOST VS SCALPEL (Clase 11)

**Objetivo:** Comparar resultados de Foremost y Scalpel sobre la misma imagen.

### Paso 1: Recuperar con Foremost
```bash
sudo apt install foremost
foremost -i /ruta/a/evidencia.raw -o ~/forense_practica/clase11_foremost
```

### Paso 2: Recuperar con Scalpel (perfil general)
```bash
forensic_suite carve /ruta/a/evidencia.raw \
  -p general \
  -o ~/forense_practica/clase11_scalpel \
  -m
```

### Paso 3: Contar archivos
```bash
echo "=== Foremost ==="
find ~/forense_practica/clase11_foremost -type f | wc -l

echo "=== Scalpel ==="
find ~/forense_practica/clase11_scalpel -type f | grep -v audit.txt | grep -v carving_manifest | wc -l
```

**Preguntas:**
- ¿Cual fue mas rapido?
- ¿Cual recupero mas archivos?
- ¿Cual permite mas control sobre que tipos buscar?

---

## EJERCICIO 13: TRIAJE CON BULK EXTRACTOR (Clase 11)

**Objetivo:** Extraer indicadores de compromiso de una imagen forense.

### Paso 1: Instalar Bulk Extractor
```bash
sudo apt install bulk-extractor
```

### Paso 2: Ejecutar sobre la imagen
```bash
bulk_extractor -o ~/forense_practica/clase11_bulk /ruta/a/evidencia.raw
```

### Paso 3: Analizar resultados
```bash
ls ~/forense_practica/clase11_bulk/
wc -l ~/forense_practica/clase11_bulk/email.txt
wc -l ~/forense_practica/clase11_bulk/url.txt
wc -l ~/forense_practica/clase11_bulk/ip.txt
```

**Preguntas:**
- ¿Que tipo de artefactos encontro?
- ¿Encontro correos, URLs o IPs?
- ¿Como combinarias Bulk Extractor con Scalpel en un caso real?

---

## EJERCICIO 14: BUSQUEDA DE CADENAS CON STRINGS Y GREP (Clase 11)

**Objetivo:** Extraer texto legible de un volcado de memoria y filtrar informacion relevante.

### Paso 1: Extraer cadenas de la memoria
```bash
strings -n 8 /ruta/a/memoria.raw > ~/forense_practica/clase11_cadenas.txt
```

### Paso 2: Extraer cadenas Unicode
```bash
strings -e l -n 8 /ruta/a/memoria.raw > ~/forense_practica/clase11_cadenas_u.txt
```

### Paso 3: Buscar correos
```bash
grep -Eio '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' \
  ~/forense_practica/clase11_cadenas.txt > ~/forense_practica/clase11_emails.txt
```

### Paso 4: Buscar URLs
```bash
grep -Eio 'https?://[^ ]+' \
  ~/forense_practica/clase11_cadenas.txt > ~/forense_practica/clase11_urls.txt
```

### Paso 5: Buscar IPs
```bash
grep -Eio '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' \
  ~/forense_practica/clase11_cadenas.txt > ~/forense_practica/clase11_ips.txt
```

### Paso 6: Buscar contexto de mensajeria
```bash
grep -B2 -A2 -i "whatsapp\|telegram\|chat\|mensaje" \
  ~/forense_practica/clase11_cadenas_u.txt > ~/forense_practica/clase11_contexto.txt
```

**Preguntas:**
- ¿Por que es importante extraer cadenas Unicode de la memoria RAM?
- ¿Que falsos positivos encontraste?
- ¿Como mejorarias las expresiones regulares para reducir ruido?

---

## EJERCICIO 15: PERFIL QUIRURGICO PARA UN CASO REAL (Clase 11)

**Objetivo:** Disenar un perfil de Scalpel para un caso especifico y documentar el proceso.

### Escenarios (elige uno)

- **A**: Caso de acoso en redes sociales. Buscar imagenes, capturas de pantalla y conversaciones.
- **B**: Caso de fraude financiero. Buscar documentos Excel/PDF, correos y bases de datos.
- **C**: Caso de espionaje corporativo. Buscar archivos ZIP/RAR/PDF con datos sensibles.
- **D**: Caso de malware. Buscar ejecutables, scripts de PowerShell y logs.

### Paso 1: Crear el perfil personalizado
```bash
nano ~/forense_practica/mi_perfil.conf
```

Ejemplo para el caso A:
```text
jpg     y   50000000    \xff\xd8\xff\xe0    \xff\xd9
png     y   50000000    \x89PNG\r\n\x1a\n   \x00\x00\x00\x00IEND\xae\x42\x60\x82
pdf     y   50000000    %PDF                %EOF\n
# Base de datos SQLite de mensajeria
sqlite  y   100000000   SQLite format 3
```

### Paso 2: Ejecutar con ForensicSuite
```bash
forensic_suite carve /ruta/a/evidencia.raw \
  -c ~/forense_practica/mi_perfil.conf \
  -o ~/forense_practica/caso_personalizado \
  -m
```

### Paso 3: Documentar
```bash
# Crear estructura de caso
mkdir -p ~/forense_practica/CASO_PERSONAL/{IMAGEN,RECUPERADOS,INFORME,AUDITORIA}

# Mover resultados
mv ~/forense_practica/caso_personalizado/* ~/forense_practica/CASO_PERSONAL/RECUPERADOS/

# Calcular hashes
cd ~/forense_practica/CASO_PERSONAL
cat > INFORME/notas.txt << EOF
Caso: [describir]
Perfil utilizado: mi_perfil.conf
Herramienta: Scalpel via ForensicSuite
Fecha: $(date)
Observaciones:
- [completar]
EOF
```

**Preguntas:**
- ¿Por que elegiste esos tipos de archivo?
- ¿Como justificarias el perfil ante un tribunal?
- ¿Que comandos adicionales usarias (Bulk Extractor, strings, grep)?

---

## VERIFICACION FINAL

Despues de completar todos los ejercicios, debes poder:

- [ ] Calcular SHA-256/SHA-512/MD5
- [ ] Verificar integridad con hash
- [ ] Listar dispositivos conectados
- [ ] Bloquear escritura en dispositivo
- [ ] Verificar que el bloqueo funciona
- [ ] Clonar un dispositivo bit a bit
- [ ] Generar cadena de custodia
- [ ] Firmar con GPG
- [ ] Obtener sello de tiempo
- [ ] Recuperar archivos eliminados
- [ ] Configurar Scalpel con archivos `.conf` personalizados
- [ ] Diferenciar Foremost, Scalpel y Bulk Extractor
- [ ] Ejecutar triaje con Bulk Extractor
- [ ] Extraer cadenas con `strings` y filtrar con `grep` y expresiones regulares
- [ ] Analizar memoria con Volatility
- [ ] Ejecutar proceso forense completo

**Si puedes hacer todo esto, estas listo para trabajar en casos reales.**

---

**FIN DE LOS EJERCICIOS**
