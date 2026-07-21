# FORENSIC SUITE - PSEUDOCODIGO
# Documento Logico para Compartir

**Version:** 2.0.0
**Objetivo:** Explicar la logica de la herramienta sin codigo especifico

---

## ESTRUCTURA GENERAL

```
FORENSIC SUITE
├── ENTRADA: Usuario ejecuta comando
├── PROCESO: modulo ejecuta operacion
├── SALIDA: resultado en pantalla o archivo
└── ERROR: mensaje de error si falla
```

---

## MODULO 1: DISPOSITIVO (Bloqueo de Escritura)

```
FUNCION bloquear_dispositivo(dispositivo)
    ENTRADA: ruta del dispositivo (ej: /dev/sdb)
    
    // Paso 1: Verificar que existe
    SI dispositivo NO existe ENTONCES
        MOSTRAR "Dispositivo no encontrado"
        FIN
    
    // Paso 2: Verificar que es bloqueable
    SI dispositivo ES disco_sistema ENTONCES
        MOSTRAR "ADVERTENCIA: No bloquear disco del sistema"
        FIN
    
    // Paso 3: Bloquear con hdparm (solo SATA, opcional/legacy)
    SI dispositivo ES SATA ENTONCES
        EJECUTAR "hdparm -r1 dispositivo"
        SI fallo ENTONCES
            MOSTRAR "hdparm no funciono (normal en USB/NVMe/SSD)"
        FIN
    
    // Paso 4: Bloquear con kernel (principal)
    EJECUTAR "blockdev --setro dispositivo"
    
    // Paso 5: Verificar bloqueo de forma PASIVA
    // No escribir en el dispositivo de evidencia
    resultado = EJECUTAR "blockdev --getro dispositivo"
    opciones_montaje = EJECUTAR "findmnt -n -o OPTIONS dispositivo"
    SI resultado == 1 Y opciones_montaje contiene "ro" ENTONCES
        MOSTRAR "Dispositivo bloqueado correctamente"
        RETORNAR exito
    SINO
        MOSTRAR "Error: No se pudo bloquear"
        RETORNAR error
    FIN
FIN

FUNCION desbloquear_dispositivo(dispositivo)
    EJECUTAR "blockdev --setrw dispositivo"
    MOSTRAR "Dispositivo desbloqueado"
FIN

FUNCION listar_dispositivos()
    ENTRADA: ninguna
    
    // Paso 1: Obtener lista de discos
    discos = EJECUTAR "lsblk -o NAME,SIZE,TYPE,MODEL"
    
    // Paso 2: Para cada disco
    PARA cada disco EN discos
        nombre = disco.nombre
        tamano = disco.tamano
        tipo = disco.tipo
        modelo = disco.modelo
        
        // Verificar si esta bloqueado
        bloqueado = EJECUTAR "blockdev --getro /dev/nombre"
        SI bloqueado == 1 ENTONCES
            estado = "BLOQUEADO"
        SINO
            estado = ""
        FIN
        
        MOSTRAR nombre, tamano, tipo, modelo, estado
    FIN
FIN
```

---

## MODULO 2: HASHER (Calculo de Hashes)

```
FUNCION calcular_hash(archivo)
    ENTRADA: ruta del archivo
    
    // Paso 1: Verificar que existe
    SI archivo NO existe ENTONCES
        MOSTRAR "Archivo no encontrado"
        FIN
    
    // Paso 2: Obtener tamano
    tamano = EJECUTAR "stat -c %s archivo"
    
    // Paso 3: Calcular SHA-256
    sha256 = EJECUTAR "sha256sum archivo"
    
    // Paso 4: Calcular SHA-512
    sha512 = EJECUTAR "sha512sum archivo"
    
    // Paso 5: Calcular MD5
    md5 = EJECUTAR "md5sum archivo"
    
    // Paso 6: Mostrar resultados
    MOSTRAR "Archivo: " archivo
    MOSTRAR "Tamano: " tamano " bytes"
    MOSTRAR "SHA-256: " sha256
    MOSTRAR "SHA-512: " sha512
    MOSTRAR "MD5: " md5
    
    RETORNAR {sha256, sha512, md5}
FIN

FUNCION generar_archivo_hash_seguro(archivo)
    ENTRADA: ruta del archivo
    
    // Paso 1: Calcular los 3 hashes
    hashes = calcular_hash(archivo)
    
    // Paso 2: Crear contenido del archivo .hash
    contenido = ""
    contenido += "# ForensicSuite Hash Verification\n"
    contenido += "# Fecha: " + FECHA_ACTUAL + "\n"
    contenido += "# Archivo: " + NOMBRE_ARCHIVO + "\n"
    contenido += "# Tamano: " + TAMANO + " bytes\n"
    contenido += "SHA256: " + hashes.sha256 + "\n"
    contenido += "SHA512: " + hashes.sha512 + "\n"
    contenido += "MD5: " + hashes.md5 + "\n"
    
    // Paso 3: Guardar archivo
    ruta_hash = archivo + ".hash"
    ESCRIBIR ruta_hash CON contenido
    
    // Paso 4: Marcar como SOLO LECTURA (critico)
    EJECUTAR "chmod 444 ruta_hash"
    
    // Paso 5: Firmar con GPG si esta disponible
    SI GPG_DISPONIBLE ENTONCES
        EJECUTAR "gpg --batch --yes --detach-sign ruta_hash"
        MOSTRAR "Firma GPG: " + ruta_hash + ".sig"
    FIN
    
    MOSTRAR "Archivo hash: " + ruta_hash
    MOSTRAR "Estado: Solo lectura (protegido)"
    
    RETORNAR ruta_hash
FIN

FUNCION verificar_archivo_hash(ruta_hash)
    ENTRADA: ruta al archivo .hash
    
    // Paso 1: Leer archivo .hash
    SI ruta_hash NO existe ENTONCES
        MOSTRAR "Error: Archivo hash no encontrado"
        FIN
    
    contenido = LEER_ARCHIVO(ruta_hash)
    
    // Paso 2: Extraer hashes y metadata
    hashes_esperados = {}
    metadata = {}
    PARA cada linea EN contenido
        SI linea EMPIEZA_CON "#" ENTONCES
            SI linea CONTIENE "Fecha:" ENTONCES
                metadata.fecha = EXTRAER(linea)
            SI linea CONTIENE "Archivo:" ENTONCES
                metadata.archivo = EXTRAER(linea)
        SI linea EMPIEZA_CON "SHA256:" ENTONCES
            hashes_esperados.sha256 = EXTRAER(linea)
        SI linea EMPIEZA_CON "SHA512:" ENTONCES
            hashes_esperados.sha512 = EXTRAER(linea)
        SI linea EMPIEZA_CON "MD5:" ENTONCES
            hashes_esperados.md5 = EXTRAER(linea)
    FIN
    
    // Paso 3: Encontrar archivo original
    ruta_original = DIRECTORIO + "/" + metadata.archivo
    SI ruta_original NO existe ENTONCES
        MOSTRAR "Error: Archivo original no encontrado"
        FIN
    
    // Paso 4: Recalcular hashes del original
    hashes_actuales = calcular_hash(ruta_original)
    
    // Paso 5: Comparar
    verificaciones = {
        "sha256": hashes_actuales.sha256 == hashes_esperados.sha256,
        "sha512": hashes_actuales.sha512 == hashes_esperados.sha512,
        "md5": hashes_actuales.md5 == hashes_esperados.md5
    }
    
    // Paso 6: Verificar firma GPG
    firma_valida = NULO
    SI ruta_hash + ".sig" existe ENTONCES
        resultado = EJECUTAR "gpg --verify ruta_hash.sig ruta_hash"
        firma_valida = resultado == EXITO
    FIN
    
    // Paso 7: Mostrar resultados
    MOSTRAR "VERIFICACION AUTOMATICA DE HASHES"
    MOSTRAR "Archivo original: " + ruta_original
    MOSTRAR "Fecha de firmado: " + metadata.fecha
    
    PARA cada algoritmo EN verificaciones
        estado = "OK" SI verificaciones[algoritmo] SINO "FALLO"
        MOSTRAR algoritmo + ": " + estado
    FIN
    
    SI firma_valida != NULO ENTONCES
        estado_firma = "VALIDA" SI firma_valida SINO "INVALIDA"
        MOSTRAR "Firma GPG: " + estado_firma
    FIN
    
    SI TODOS verificaciones VERDADEROS ENTONCES
        MOSTRAR "RESULTADO: INTEGRIDAD VERIFICADA"
        RETORNAR exito
    SINO
        MOSTRAR "RESULTADO: INTEGRIDAD COMPROMETIDA"
        RETORNAR error
    FIN
FIN

FUNCION verificar_integridad(archivo, hash_esperado)
    ENTRADA: archivo y hash a comparar
    
    // Calcular hash actual
    hash_actual = calcular_hash(archivo).sha256
    
    // Comparar
    SI hash_actual == hash_esperado ENTONCES
        MOSTRAR "INTEGRIDAD: VERIFICADA"
        RETORNAR verdadero
    SINO
        MOSTRAR "INTEGRIDAD: COMPROMETIDA"
        RETORNAR falso
    FIN
FIN
```

---

## MODULO 3: CADENA DE CUSTODIA

```
FUNCION crear_acta(archivo, datos_perito, caso)
    ENTRADA: archivo de evidencia, datos del perito, numero de caso
    
    // Paso 1: Calcular hash de la evidencia
    hashes = calcular_hash(archivo)
    
    // Paso 2: Obtener fecha/hora actual
    fecha = OBTENER_FECHA_ACTUAL()
    hora = OBTENER_HORA_ACTUAL()
    
    // Paso 3: Crear estructura del acta
    acta = {
        "identificacion": {
            "numero": generar_numero_acta(),
            "fecha": fecha,
            "hora": hora,
            "lugar": datos_perito.lugar
        },
        "colector": {
            "nombre": datos_perito.nombre,
            "cedula": datos_perito.cedula,
            "cargo": datos_perito.cargo,
            "autoridad": caso.autoridad
        },
        "evidencia": {
            "tipo": detectar_tipo(archivo),
            "nombre": archivo.nombre,
            "tamano": archivo.tamano,
            "hash_sha256": hashes.sha256,
            "hash_sha512": hashes.sha512,
            "hash_md5": hashes.md5
        },
        "metodo": {
            "bloqueo": "blockdev --setro",
            "clonado": "dcfldd bs=4M",
            "verificacion": "SHA-256 + SHA-512 + MD5"
        }
    }
    
    // Paso 4: Guardar en archivo
    nombre_archivo = archivo + ".acta.json"
    ESCRIBIR nombre_archivo CON acta
    
    // Paso 5: Calcular hash del acta
    hash_acta = calcular_hash(nombre_archivo)
    
    MOSTRAR "Acta generada: " nombre_archivo
    MOSTRAR "SHA-256 acta: " hash_acta.sha256
    
    RETORNAR nombre_archivo
FIN
```

---

## MODULO 4: FIRMA GPG

```
FUNCION firmar_archivo(archivo)
    ENTRADA: archivo a firmar
    
    // Paso 1: Verificar que existe
    SI archivo NO existe ENTONCES
        MOSTRAR "Archivo no encontrado"
        FIN
    
    // Paso 2: Verificar que hay clave GPG
    claves = EJECUTAR "gpg --list-secret-keys"
    SI claves VACIO ENTONCES
        MOSTRAR "No hay claves GPG. Generar con: gpg --full-generate-key"
        FIN
    
    // Paso 3: Firmar
    EJECUTAR "gpg --detach-sign archivo"
    
    // Paso 4: Verificar que se creo la firma
    SI archivo + ".sig" existe ENTONCES
        MOSTRAR "Firma generada: " archivo + ".sig"
        RETORNAR exito
    SINO
        MOSTRAR "Error al generar firma"
        RETORNAR error
    FIN
FIN

FUNCION verificar_firma(archivo)
    ENTRADA: archivo con firma
    
    // Verificar firma
    resultado = EJECUTAR "gpg --verify archivo.sig archivo"
    
    SI resultado CONTIENE "Good signature" ENTONCES
        MOSTRAR "Firma: VALIDA"
        MOSTRAR "Firmante: " extraer_firmante(resultado)
        RETORNAR verdadero
    SINO
        MOSTRAR "Firma: INVALIDA"
        RETORNAR falso
    FIN
FIN
```

---

## MODULO 5: TIMESTAMP (Sello de Tiempo)

```
FUNCION obtener_timestamp(archivo)
    ENTRADA: archivo a sellevar
    
    // Paso 1: Crear solicitud
    EJECUTAR "openssl ts -query -data archivo -sha256 -out archivo.tsq"
    
    // Paso 2: Enviar a TSA (Time Stamping Authority)
    resultado = EJECUTAR "curl -s -H 'Content-Type: application/timestamp-query' 
                          --data-binary @archivo.tsq 
                          http://timestamp.digicert.com"
    
    // Paso 3: Guardar respuesta
    ESCRIBIR archivo + ".tsr" CON resultado
    
    // Paso 4: Verificar
    EJECUTAR "openssl ts -verify -data archivo -in archivo.tsr -CAfile cacert.pem"
    
    MOSTRAR "Sello de tiempo: " archivo + ".tsr"
    MOSTRAR "TSA: DigiCert"
    MOSTRAR "Fecha: " OBTENER_FECHA_ACTUAL()
    
    RETORNAR archivo + ".tsr"
FIN
```

---

## MODULO 6: MANIFEST

```
FUNCION generar_manifest(directorio, caso, perito)
    ENTRADA: directorio a inventariar, caso, perito
    
    // Paso 1: Escanear directorio
    archivos = LISTAR_ARCHIVOS(directorio)
    
    // Paso 2: Para cada archivo, calcular hashes
    lista_archivos = []
    PARA cada archivo EN archivos
        hashes = calcular_hash(archivo)
        elemento = {
            "nombre": archivo.nombre,
            "ruta": archivo.ruta_completa,
            "tamano": archivo.tamano,
            "sha256": hashes.sha256,
            "sha512": hashes.sha512,
            "md5": hashes.md5
        }
        AGREGAR elemento A lista_archivos
    FIN
    
    // Paso 3: Crear manifest
    manifest = {
        "caso": caso,
        "fecha": OBTENER_FECHA_ACTUAL(),
        "perito": perito,
        "total_archivos": LONGITUD(lista_archivos),
        "tamano_total": SUMAR_TAMANOS(lista_archivos),
        "archivos": lista_archivos
    }
    
    // Paso 4: Guardar
    ESCRIBIR directorio + "/manifest.json" CON manifest
    
    // Paso 5: Calcular hash del manifest
    hash_manifest = calcular_hash(directorio + "/manifest.json")
    
    MOSTRAR "Manifest: " directorio + "/manifest.json"
    MOSTRAR "Archivos: " LONGITUD(lista_archivos)
    MOSTRAR "SHA-256: " hash_manifest.sha256
    
    RETORNAR directorio + "/manifest.json"
FIN

FUNCION verificar_manifest(manifest_json)
    ENTRADA: archivo manifest.json
    
    // Leer manifest
    manifest = LEER_JSON(manifest_json)
    
    // Verificar cada archivo
    errores = 0
    PARA cada archivo EN manifest.archivos
        SI archivo.ruta NO existe ENTONCES
            MOSTRAR "FALTA: " archivo.ruta
            errores = errores + 1
        SINO
            hash_actual = calcular_hash(archivo.ruta).sha256
            SI hash_actual != archivo.sha256 ENTONCES
                MOSTRAR "ALTERADO: " archivo.ruta
                errores = errores + 1
            SINO
                MOSTRAR "OK: " archivo.ruta
            FIN
        FIN
    FIN
    
    SI errores == 0 ENTONCES
        MOSTRAR "MANIFEST VALIDO"
    SINO
        MOSTRAR "MANIFEST CON " errores + " ERRORES"
    FIN
FIN
```

---

## MODULO 7: SCALPEL (File Carving)

```
FUNCION ejecutar_carving(fuente, perfil, salida)
    ENTRADA: dispositivo/imagen, perfil de configuracion, directorio salida
    
    // Paso 1: Verificar que Scalpel esta instalado
    SI "scalpel" NO existe ENTONCES
        MOSTRAR "Scalpel no instalado. Ejecutar: apt install scalpel"
        FIN
    
    // Paso 2: Seleccionar configuracion segun perfil
    SESEGUN perfil
        CASO "recuperacion":
            config = "configs/recuperacion.conf"
        CASO "cripto":
            config = "configs/cripto.conf"
        CASO "medios":
            config = "configs/medios.conf"
        CASO "documentos":
            config = "configs/documentos.conf"
        CASO "redes":
            config = "configs/redes.conf"
        CASO "general":
            config = "configs/general.conf"
    FINSEGUN
    
    // Paso 3: Verificar que la fuente existe
    SI fuente NO existe ENTONCES
        MOSTRAR "Fuente no encontrada"
        FIN
    
    // Paso 4: Ejecutar Scalpel
    EJECUTAR "scalpel -c config fuente -o salida"
    
    // Paso 5: Contar archivos recuperados
    archivos_recuperados = LISTAR_ARCHIVOS(salida)
    
    // Paso 6: Calcular hashes de archivos recuperados
    PARA cada archivo EN archivos_recuperados
        hashes = calcular_hash(archivo)
        MOSTRAR archivo.nombre, archivo.tamano, hashes.sha256
    FIN
    
    // Paso 7: Generar manifest si se pidio
    SI manifest_solicitado ENTONCES
        generar_manifest(salida, caso, perito)
    FIN
    
    MOSTRAR "Archivos recuperados: " LONGITUD(archivos_recuperados)
FIN
```

---

## MODULO 8: MEMORIA (Volcado RAM)

```
FUNCION verificar_entorno_memoria()
    ENTRADA: ninguna
    
    // Verificar componentes
    resultado = {
        "mforense": EXISTE("mforense"),
        "root": USUARIO_ES_ROOT(),
        "lime": EXISTE("/lib/modules/.../lime.ko"),
        "avml": EXISTE("/usr/local/bin/avml"),
        "volatility": EXISTE("volatility3")
    }
    
    MOSTRAR "ENTORNO DE MEMORIA FORENSE"
    MOSTRAR "mforense: " resultado.mforense
    MOSTRAR "Root: " resultado.root
    MOSTRAR "LiME: " resultado.lime
    MOSTRAR "AVML: " resultado.avml
    MOSTRAR "Volatility: " resultado.volatility
    
    RETORNAR resultado
FIN

FUNCION adquirir_memoria(caso)
    ENTRADA: ID del caso
    
    // Paso 1: Verificar que es root
    SI NO USUARIO_ES_ROOT() ENTONCES
        MOSTRAR "Ejecutar con sudo"
        FIN
    
    // Paso 2: Ejecutar mforense
    EJECUTAR "mforense acquire"
    
    // Paso 3: Verificar que se creo el dump
    dumps = LISTAR_ARCHIVOS("*.raw")
    SI dumps VACIO ENTONCES
        MOSTRAR "Error: No se genero dump"
        FIN
    
    // Paso 4: Calcular hashes
    PARA cada dump EN dumps
        hashes = calcular_hash(dump)
        MOSTRAR "Dump: " dump
        MOSTRAR "SHA-256: " hashes.sha256
    FIN
    
    RETORNAR dumps[0]
FIN

FUNCION analizar_memoria(dump, plugin)
    ENTRADA: archivo dump, plugin de Volatility
    
    // Verificar que Volatility esta disponible
    SI NO EXISTE("volatility3") ENTONCES
        MOSTRAR "Volatility no instalado"
        FIN
    
    // Ejecutar analisis
    resultado = EJECUTAR "volatility3 -f dump plugin"
    
    MOSTRAR resultado
    RETORNAR resultado
FIN
```

---

## MODULO 9: PERITO (Configuracion)

```
FUNCION configurar_perito()
    ENTRADA: datos del usuario
    
    // Solicitar datos
    nombre = PEDIR "Nombre completo"
    cedula = PEDIR "Cedula de identidad"
    cargo = PEDIR "Cargo o titulo"
    email = PEDIR "Email"
    clave_gpg = PEDIR "ID de clave GPG"
    
    // Crear configuracion
    configuracion = {
        "nombre": nombre,
        "cedula": cedula,
        "cargo": cargo,
        "email": email,
        "clave_gpg": clave_gpg,
        "fecha_configuracion": OBTENER_FECHA_ACTUAL()
    }
    
    // Guardar
    directorio = HOME + "/.forensic_suite/"
    CREAR_DIRECTORIO(directorio)
    ESCRIBIR directorio + "/perito.conf" CON configuracion
    
    MOSTRAR "Configuracion guardada en " directorio + "/perito.conf"
    RETORNAR configuracion
FIN

FUNCION cargar_perito()
    ENTRADA: ninguna
    
    archivo = HOME + "/.forensic_suite/perito.conf"
    SI archivo NO existe ENTONCES
        MOSTRAR "No hay configuracion. Ejecutar: forensic_suite perito --configurar"
        RETORNAR NULO
    FIN
    
    configuracion = LEER_JSON(archivo)
    MOSTRAR "Perito: " configuracion.nombre
    MOSTRAR "Cedula: " configuracion.cedula
    MOSTRAR "Cargo: " configuracion.cargo
    RETORNAR configuracion
FIN
```

---

## FLUJO PRINCIPAL (CLI)

```
PROGRAMA forensic_suite
    
    // Leer comando del usuario
    comando = ARGV[1]
    argumentos = ARGV[2...]
    
    SEGUN comando
        CASO "hash":
            calcular_hash(argumentos[0])
        
        CASO "verificar":
            verificar_integridad(argumentos[0], argumentos[1])
        
        CASO "bloquear":
            bloquear_dispositivo(argumentos[0])
        
        CASO "desbloquear":
            desbloquear_dispositivo(argumentos[0])
        
        CASO "listar":
            listar_dispositivos()
        
        CASO "acta":
            crear_acta(argumentos[0], datos_perito, caso)
        
        CASO "firmar":
            firmar_archivo(argumentos[0])
        
        CASO "verificar-firma":
            verificar_firma(argumentos[0])
        
        CASO "timestamp":
            obtener_timestamp(argumentos[0])
        
        CASO "manifest":
            generar_manifest(argumentos[0], caso, perito)
        
        CASO "carve":
            ejecutar_carving(argumentos[0], perfil, salida)
        
        CASO "memoria":
            SI argumentos CONTIENE "--adquirir" ENTONCES
                adquirir_memoria(caso)
            SINO SI argumentos CONTIENE "--analizar" ENTONCES
                analizar_memoria(dump, plugin)
            SINO SI argumentos CONTIENE "--verificar-entorno" ENTONCES
                verificar_entorno_memoria()
            FIN
        
        CASO "perito":
            SI argumentos CONTIENE "--configurar" ENTONCES
                configurar_perito()
            SINO
                cargar_perito()
            FIN
        
        CASO "daemon":
            EJECUTAR "forensic_blockerd " + argumentos[0]
        
        CASO DEFAULT:
            MOSTRAR "Comando no reconocido"
            MOSTRAR "Usar: forensic_suite --help"
    FINSEGUN
    
FIN PROGRAMA
```

---

## DIAGRAMA DE FLUJO GENERAL

```
                    INICIO
                       │
                       ▼
              ┌─────────────────┐
              │  Leer comando   │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  validar inputs │
              └────────┬────────┘
                       │
                       ▼
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
   ┌───────────┐             ┌───────────┐
   │  Existe?  │             │ Es root?  │
   └─────┬─────┘             └─────┬─────┘
         │                         │
    SI   │   NO               SI   │   NO
    │    │    │               │    │    │
    ▼    │    ▼               ▼    │    ▼
  OK    │  ERROR             OK    │  ERROR
         │                           │
         └─────────────┬─────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Ejecutar       │
              │  operacion      │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Calcular       │
              │  hashes         │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Guardar        │
              │  resultados     │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │  Mostrar        │
              │  salida         │
              └────────┬────────┘
                       │
                       ▼
                      FIN
```

---

## TABLA DE VERDAD: CUANDO USAR CADA COMANDO

```
SITUACION                          COMANDO
─────────────────────────────────────────────────────────
Recien llegas a la escena          forensic_suite listar
Encontraste un dispositivo         forensic_suite bloquear /dev/sdX
Vas a clonar evidencia             forensic_suite bloquear + dcfldd
Terminaste de clonar               forensic_suite hash evidencia.raw
Necesitas documentar               forensic_suite acta evidencia.raw
Quieres firmar evidencia           forensic_suite firmar archivo
Necesitas probar fecha             forensic_suite timestamp archivo
Vas a recuperar archivos           forensic_suite carve fuente -p perfil
Hay memoria RAM que capturar        forensic_suite memoria --adquirir
Quieres analizar memoria           forensic_suite memoria --analizar --dump
Configurar tus datos               forensic_suite perito --configurar
```

---

## ERRORES COMUNES Y SOLUCIONES

```
ERROR                           CAUSA                      SOLUCION
────────────────────────────────────────────────────────────────────
"Permission denied"              No es root                 Agregar sudo
"Device not found"               USB no conectado           Reconectar
"Scalpel not found"              No instalado               apt install scalpel
"GPG error"                      No hay claves              gpg --full-generate-key
"AVML not found"                 No instalado               Descargar de GitHub
"Read-only file system"          Bloqueo funciona           Correcto, esta bloqueado
"No such device"                 hdparm no soporta USB      Usar blockdev
```

---

## REFERENCIA RAPIDA

```
COMANDO                          QUE HACE
─────────────────────────────────────────────────────────
forensic_suite hash              Calcula SHA-256/SHA-512/MD5
forensic_suite verificar         Compara hash con esperado
forensic_suite bloquear          Impide escritura en disco
forensic_suite desbloquear       Permite escritura
forensic_suite listar            Muestra dispositivos
forensic_suite acta              Crea cadena de custodia
forensic_suite firmar            Firma con GPG
forensic_suite verificar-firma   Verifica firma GPG
forensic_suite timestamp         Sello de tiempo RFC 3161
forensic_suite manifest          Inventario de archivos
forensic_suite carve             Recupera archivos eliminados
forensic_suite memoria           Volcado/analisis RAM
forensic_suite perito            Configurar experto
forensic_suite daemon            Servicio de bloqueo
```

---

**FIN DEL PSEUDOCODIGO**

Este documento explica la LOGICA sin usar un lenguaje de programacion especifico.
Cualquier persona con conocimientos basicos puede entenderlo y reimplementarlo.

---

## FLUJO SEGURO DE HASHES

### Como funciona el almacenamiento seguro

```
1. CALCULAR HASHES
   forensic_suite hash evidencia.raw -g

2. CREAR ARCHIVO SEGURO
   Se genera: evidencia.raw.hash
   Contiene: SHA256, SHA512, MD5
   Permisos: 444 (solo lectura)
   Firma: GPG (automatica)

3. VERIFICAR AUTOMATICAMENTE
   forensic_suite verificar evidencia.raw.hash

4. RESULTADO
   Compara los 3 hashes
   Verifica firma GPG
   Muestra OK o FALLO
```

### Por que es seguro

```
ARCHIVO .hash CONTIENE:
├── Hash SHA-256 (64 caracteres)
├── Hash SHA-512 (128 caracteres)
├── Hash MD5 (32 caracteres)
├── Fecha de creacion
├── Nombre del archivo original
└── Tamano del archivo original

PROTECCIONES:
├── Permisos 444 (solo lectura)
├── Firma GPG (no repudiable)
├── 3 algoritmos (redundancia)
└── Timestamp (fecha verificable)
```

### Ejemplo completo

```bash
# Paso 1: Generar hashes seguros
forensic_suite hash evidencia.raw -g
# Salida:
#   Archivo hash: evidencia.raw.hash
#   Estado: Solo lectura (protegido)
#   Firma GPG: evidencia.raw.hash.sig

# Paso 2: Verificar integridad
forensic_suite verificar evidencia.raw.hash
# Salida:
#   VERIFICACION AUTOMATICA DE HASHES
#   ==================================
#   SHA256   OK       a17dcdfd36f47303...
#   SHA512   OK       04f0df590d7614f1...
#   MD5      OK       940cbe15c94d7e33...
#   
#   RESULTADO: INTEGRIDAD VERIFICADA

# Paso 3: Si alguien modifico el archivo
echo "ALTERADO" > evidencia.raw
forensic_suite verificar evidencia.raw.hash
# Salida:
#   SHA256   FALLO    a17dcdfd... = 14f5507b...
#   SHA512   FALLO    04f0df59... = ac9555e4...
#   MD5      FALLO    940cbe15... = 165802b6...
#   
#   RESULTADO: INTEGRIDAD COMPROMETIDA
```
