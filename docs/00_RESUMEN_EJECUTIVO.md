# 00 - Resumen Ejecutivo

**ForensicSuite v1.0.0** | Framework de Analisis Forense Digital
Autor: Tr3w01 | Python 3.9+ | Venezuela

---

## Que es ForensicSuite

Suite de herramientas Python que automatiza las operaciones criticas de la investigacion forense digital:

1. Bloqueo de escritura antes de que el SO toque el dispositivo
2. Hashes triples (SHA-256 + SHA-512 + MD5) en una sola pasada
3. Cadena de custodia conforme al Manual MP 2017
4. Firma digital y sello de tiempo para evidencia
5. Manifest verificable de integridad de archivos

## Modulos

| Modulo | Funcion |
|---|---|
| `dispositivo` | Bloqueo de escritura 4 capas (hdparm/blockdev/losetup/mount) |
| `hasher` | SHA-256 + SHA-512 + MD5 simultaneos |
| `cadena_custodia` | Acta MP 2017 (6 secciones) |
| `firma_gpg` | Firma detached GPG (.asc) |
| `timestamp` | Sello RFC 3161 via TSA |
| `manifest` | JSON canonico verificable |
| `perito` | Configuracion del experto |
| `daemon` | Bloqueo automatico al conectar disco |

## Documentacion disponible

| Documento | Para quien | Contenido |
|---|---|---|
| `01_GUIA_USUARIO.md` | Perito que usa la herramienta | Pasos para usar en campo |
| `02_GUIA_TECNICA.md` | Auditor tecnico | Detalle de implementacion, algoritmos, API |
| `03_PROTOCOLO_FORENSE.md` | Perito y contra perito | Protocolo paso a paso conforme a normas |
| `04_VERIFICACION_CONTRA_PERITAJE.md` | Contra perito | Como verificar los resultados de forma independiente |
| `05_MARCO_LEGAL.md` | Jurista y perito | Fundamento legal en Venezuela |
| `06_VALIDACION_HERRAMIENTAS.md` | Auditor | Validacion de integridad de la propia herramienta |
