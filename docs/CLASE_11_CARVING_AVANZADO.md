# CLASE 11: Carving Avanzado con Scalpel, Bulk Extractor y Expresiones Regulares

> Contenido extraido de la clase 11 de la CERTIFICACIÓN EN INFORMÁTICA FORENSE 2026, ofrecida por [Lazarus Venezuela](https://www.lazarus.com.ve/).

## Objetivos de la Clase

- Comprender la diferencia entre carving, triaje y extraccion masiva de artefactos.
- Configurar Scalpel mediante archivos `.conf` para busquedas quirurgicas.
- Usar `strings` + `grep` con expresiones regulares para extraer informacion relevante.
- Saber cuando usar Foremost, Scalpel o Bulk Extractor.

---

## 1. Conceptos Fundamentales

### File Carving (Tallado de Archivos)

Tecnica que recupera archivos a partir de un flujo de bytes sin depender del sistema de archivos (NTFS, FAT32, EXT4, etc.).

- Busca **headers** (cabeceras / numeros magicos).
- Busca **footers** (pies de pagina / finales).
- Extrae el bloque comprendido entre ambos.

> Importante: cuando un usuario "borra" un archivo, el sistema operativo suele eliminar unicamente la referencia. Los datos siguen en el disco hasta que se sobrescriben.

### Expresiones Regulares

Permiten buscar patrones dentro de grandes volumenes de datos:

- Correos electronicos
- Direcciones IP
- URLs
- Numeros de telefono
- Palabras clave contextuales

---

## 2. Scalpel

Scalpel es una reescritura de Foremost 0.69 que permite un control mucho mayor mediante archivos de configuracion.

### Ventajas de Scalpel

- Multihilo (mas rapido que Foremost).
- Altamente configurable mediante `.conf`.
- Permite expresiones regulares en las reglas.
- Ideal para crear perfiles personalizados por tipo de caso.

### Desventajas

- Requiere configuracion manual.
- No lee dentro de archivos comprimidos.
- Puede generar falsos positivos si las reglas no son precisas.

### Sintaxis de una Regla

```text
extension  case_sensitive  tamano_maximo  header  footer
```

| Campo | Significado |
|-------|-------------|
| `extension` | Extension que recibiran los archivos recuperados |
| `case_sensitive` | `y` = sensible a mayusculas / `n` = insensible |
| `tamano_maximo` | Tamano maximo en bytes |
| `header` | Firma de inicio |
| `footer` | Firma de fin |

### Ejemplos de Reglas

```text
# Imagenes JPEG (hasta 20 MB)
jpg     y   20000000    \xff\xd8\xff\xe0    \xff\xd9

# PNG (hasta 5 MB)
png     y   5000000     \x89PNG\r\n\x1a\n   \x00\x00\x00\x00IEND\xae\x42\x60\x82

# PDF (hasta 50 MB)
pdf     y   50000000    %PDF                %EOF\n
# Office moderno (ZIP interno)
docx    y   10000000    PK\x03\x04          [Content_Types].xml

# Base de datos SQLite (WhatsApp, Telegram, Signal)
sqlite  y   100000000   SQLite format 3
```

### Uso con ForensicSuite

```bash
# Ver perfiles disponibles
forensic_suite carve --perfiles

# Usar perfil de mensajeria
forensic_suite carve evidencia.raw -p mensajeria -o ./recuperados -m

# Usar configuracion personalizada
forensic_suite carve evidencia.raw -c ~/mi_perfil.conf -o ./recuperados -m
```

### Uso Manual

```bash
sudo nano /etc/scalpel/scalpel.conf

# Ejecutar
sudo scalpel -c /etc/scalpel/scalpel.conf -o ./salida/ evidencia.raw

# Ver resultados
ls -R ./salida/
```

---

## 3. Foremost

Herramienta clasica de carving por cabeceras y footers.

### Ventajas

- Muy sencilla de usar.
- No requiere configuracion para tipos comunes.

### Desventajas

- Monohilo (mas lenta).
- Menos configurable que Scalpel.
- No usa expresiones regulares.

```bash
foremost -i imagen.dd -o ./recuperados_foremost/
```

---

## 4. Bulk Extractor

Herramienta de triaje forense masivo. No recupera archivos completos; extrae indicadores de compromiso (IoC) y metadatos.

### Ventajas

- Extremadamente rapido (divide la imagen en bloques de 16 MB y procesa en paralelo).
- Incluye validacion semantica (reduce ruido).
- Lee dentro de archivos comprimidos.
- Extrae: correos, URLs, IPs, MACs, tarjetas de credito, EXIF, GPS, etc.

### Desventajas

- No recupera archivos originales intactos.
- Genera grandes volumenes de texto que requieren post-procesamiento.

```bash
bulk_extractor -o ./salida_be/ imagen.dd

# Analizar resultados
ls ./salida_be/
cat ./salida_be/email.txt
```

---

## 5. Cuadro Comparativo

| Herramienta | Tipo | Uso Ideal | Fortaleza |
|-------------|------|-----------|-----------|
| **Foremost** | Carving clasico | Recuperacion simple de archivos comunes | Sencillez |
| **Scalpel** | Carving avanzado | Recuperacion quirurgica con reglas personalizadas | Configuracion y expresiones regulares |
| **Bulk Extractor** | Triaje masivo | Extraer IoC, metadatos, emails, URLs | Velocidad y paralelismo |

> Nota: En muchos casos reales se combinan las tres herramientas: Bulk Extractor para triaje rapido, Scalpel para recuperacion especifica y Foremost como respaldo.

---

## 6. Strings y Grep

Extraer cadenas legibles de cualquier archivo o volcado.

### Extraer cadenas ASCII

```bash
strings -n 8 evidencia.raw > cadenas.txt
```

### Extraer cadenas Unicode

```bash
strings -e l -n 8 memoria.raw > cadenas_unicode.txt
```

### Buscar correos electronicos

```bash
grep -Eio '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' cadenas.txt > emails.txt
```

### Buscar URLs

```bash
grep -Eio 'https?://[^ ]+' cadenas.txt > urls.txt
```

### Buscar direcciones IP

```bash
grep -Eio '\b([0-9]{1,3}\.){3}[0-9]{1,3}\b' cadenas.txt > ips.txt
```

### Buscar numeros telefonicos venezolanos

```bash
grep -Eio '\+?58[0-9]{10}|0[0-9]{10}' cadenas.txt > telefonos.txt
```

### Buscar contexto alrededor de una palabra clave

```bash
grep -B2 -A2 -i "whatsapp\|telegram\|mensaje" cadenas.txt > contexto.txt
```

---

## 7. Casos de Uso Recomendados

| Escenario | Herramienta recomendada |
|-----------|-------------------------|
| Recuperar fotos borradas de un USB | Foremost / Scalpel `-p medios` |
| Recuperar documentos de un disco danado | Scalpel `-p documentos` |
| Buscar conversaciones de WhatsApp en RAM | Scalpel `-p mensajeria` + `strings -e l` |
| Triaje rapido de una imagen de 1 TB | Bulk Extractor |
| Extraer emails/URLs dominios de un dump | Bulk Extractor + `grep` |
| Crear perfil quirurgico para un caso especifico | Scalpel con `.conf` personalizado |

---

## 8. Recomendaciones del Instructor

1. **No confiar en una sola herramienta**: combinar Foremost, Scalpel y Bulk Extractor.
2. **Documentar todo**: hashes, logs, comandos, fechas y cadena de custodia.
3. **Crear perfiles personalizados** segun el tipo de caso.
4. **Aprender expresiones regulares**: potencian drasticamente las busquedas.
5. **Pensar en pseudocodigo antes de automatizar**: define la logica, luego el codigo.

---

## 9. Comandos Clave de la Clase 11

```bash
# Instalar Scalpel
sudo apt install scalpel

# Editar configuracion
sudo nano /etc/scalpel/scalpel.conf

# Ejecutar Scalpel con perfil personalizado
sudo scalpel -c perfil.conf -o ./salida/ imagen.dd

# Ejecutar Foremost
foremost -i imagen.dd -o ./salida_foremost/

# Ejecutar Bulk Extractor
bulk_extractor -o ./salida_be/ imagen.dd

# Extraer cadenas
strings -n 8 evidencia.raw > cadenas.txt

# Buscar con regex
grep -Eio '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' cadenas.txt
```

---

## Referencias

- Scalpel 1.60 README: `/usr/share/doc/scalpel/README.md`
- Foremost: https://sourceforge.net/projects/foremost/
- Bulk Extractor: https://github.com/simsong/bulk_extractor
