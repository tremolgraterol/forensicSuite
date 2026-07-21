# GUIA: Herramientas por Plataforma

## LINUX vs WINDOWS - Cual usar y cuando

### REGLA DE ORO
Nunca instales herramientas en el equipo del sospechoso.
Nunca ejecutes analisis en el equipo del sospechoso.

---

## ESCENARIO 1: El equipo esta APAGADO

**Que haces:** Bootear desde USB forense (Linux)

```
1. Insertar USB con CAINE/KALI/SIFT
2. Prender PC y entrar a BIOS (F2/F12/DEL)
3. Seleccionar boot desde USB
4. Linux carga en memoria RAM
5. El disco del sospechoso NO se toca
6. Usar herramientas Linux normalmente
```

**Herramientas Linux para este escenario:**
- forensic_suite (nuestra)
- dd / dcfldd (clonado)
- blockdev (bloqueo)
- scalpel (carving)
- volatility (memoria)

---

## ESCENARIO 2: El equipo esta ENCENDIDO (Windows)

**Opcion A: Apagar y bootear USB (RECOMENDADO)**
```bash
# 1. NO tocar nada aun
# 2. Bootear USB CAINE
# 3. Clonar desde Linux
```

**Opcion B: Trabajar en caliente (SI NO SE PUEDE APAGAR)**

### Volcado de memoria en Windows

**Herramientas Windows (portables, sin instalar):**

```powershell
# WinPmem (descargar de GitHub)
# https://github.com/Akasora/winpmem
winpmem_mini_x64.exe memoria.raw

# DumpIt (mas simple)
# https://www.magnetforensics.com/resources/free-tools/
DumpIt.exe
# Genera: RAMDump.raw automaticamente

# FTK Imager (GUI)
# https://www.exterro.com/ftk-imager
# File > Capture Memory > Seleccionar destino > Capture
```

### Bloqueo de escritura en Windows

**Opcion 1: Hardware write-blocker (LA MEJOR)**
```
Dispositivo fisico USB ($50-500 USD)
├── Se conecta entre el USB del sospechoso y tu laptop
├── Bloquea escrituras a nivel electrico
├── No necesita drivers
└── Es aceptado en tribunales
```

**Opcion 2: Software (PARA EMERGENCIA)**
```powershell
# Regedit: Bloquear escritura en USB
# HKLM\SYSTEM\CurrentControlSet\Control\StorageDevicePolicies
# WriteProtect = 1

# O usar Diskpart
diskpart
list disk
select disk X    # X = numero del USB
attributes disk set readonly
```

**Nota:** El bloqueo por software NO es confiable para tribunales.
Siempre preferir hardware write-blocker.

---

## ESCENARIO 3: Dispositivo USB a Windows

**PROCESO CORRECTO:**

```
COMPUTADORA SOSPECHOSO          TU EQUIPO FORENSE
(Windows encendido)              (Linux con forensic_suite)
        │                              │
        │  1. Conectar write-blocker   │
        │  ◄──────────────────────────►│
        │                              │
        │  2. Bloquear en Linux        │
        │     sudo forensic_suite      │
        │     bloquear /dev/sdc        │
        │                              │
        │  3. Clonar                   │
        │     sudo dcfldd if=/dev/sdc  │
        │     of=/evidencia/usb.raw    │
        │                              │
        │  4. Hash                     │
        │     forensic_suite hash      │
        │     usb.raw                  │
        │                              │
```

**Comandos exactos:**
```bash
# En tu laptop Linux (con write-blocker conectado)
sudo forensic_suite bloquear /dev/sdc
sudo dcfldd if=/dev/sdc of=/evidencia/usb.raw bs=4M
forensic_suite hash /evidencia/usb.raw -g
forensic_suite verificar /evidencia/usb.raw.hash
forensic_suite carve /evidencia/usb.raw -p general -o /evidencia/recuperados
```

---

## ESCENARIO 4: Disco interno SATA de Windows

**PROCESO CORRECTO:**

```
OPCION A: Bootear USB Linux (RECOMENDADO)
├── Apagar PC del sospechoso
├── Bootear desde USB CAINE
├── blockdev --setro /dev/sda
├── dd if=/dev/sda of=/evidencia/disco.raw bs=4M
└── Trabajar desde Linux

OPCION B: Conectar disco a tu laptop
├── Sacar disco del PC del sospechoso
├── Conectar a tu laptop con adaptador SATA-USB
├── forensic_suite bloquear /dev/sdc
├── dcfldd if=/dev/sdc of=/evidencia/disco.raw bs=4M
└── Trabajar desde Linux
```

**NUNCA:**
- Instalar forensic_suite en Windows del sospechoso
- Ejecutar dd desde Windows
- Usar cmd.exe o PowerShell para clonar

---

## RESUMEN: Que herramienta en cada plataforma

### Para VOLCADO DE MEMORIA

| Plataforma | Herramienta | Comando |
|------------|-------------|---------|
| Linux | AVML | `sudo avml /tmp/memoria.raw` |
| Linux | LiME | `sudo insmod lime.ko "path=/tmp/memoria.lime"` |
| Linux | mforense | `sudo mforense acquire` |
| Windows | WinPmem | `winpmem_mini_x64.exe memoria.raw` |
| Windows | DumpIt | `DumpIt.exe` (automatico) |
| Windows | FTK Imager | GUI: Capture Memory |

### Para BLOQUEO DE ESCRITURA

| Plataforma | Herramienta | Metodo |
|------------|-------------|--------|
| Linux | blockdev | `sudo blockdev --setro 1 /dev/sdX` |
| Linux | hdparm | `sudo hdparm -r1 /dev/sdX` (solo SATA) |
| Windows | Write-blocker | Dispositivo fisico |
| Windows | Diskpart | `attributes disk set readonly` (no confiable) |

### Para CLONADO

| Plataforma | Herramienta | Comando |
|------------|-------------|---------|
| Linux | dcfldd | `sudo dcfldd if=/dev/sdX of=clona.raw bs=4M` |
| Linux | dd | `sudo dd if=/dev/sdX of=clona.raw bs=4M status=progress` |
| Windows | FTK Imager | GUI: Raw Disk Image |
| Windows | WinHex | GUI: Disk > Clone Disk |

### Para FILE CARVING

| Plataforma | Herramienta | Comando |
|------------|-------------|---------|
| Linux | forensic_suite | `forensic_suite carve raw -p recuperacion -o out` |
| Linux | Scalpel | `scalpel raw -o out/` |
| Linux | Foremost | `foremost -i raw -o out/` |
| Windows | Foremost | Portatil: `foremost.exe -i raw -o out/` |

### Para ANALISIS DE MEMORIA

| Plataforma | Herramienta | Comando |
|------------|-------------|---------|
| Linux | Volatility3 | `volatility3 -f memoria.raw windows.pslist` |
| Windows | Volatility3 | `vol.exe -f memoria.raw windows.pslist` |

---

## BOOT DISK FORENSE: CAINE

### Como crear USB booteable

```bash
# En Linux
# Descargar CAINE: https://www.caine-live.net/
wget https://www.caine-live.net/stable/caine_14.0.iso

# Crear USB (REEMPLAZAR sdX con tu USB)
sudo dd if=caine_14.0.iso of=/dev/sdX bs=4M status=progress

# O usar Etcher (GUI)
# https://etcher.balena.io/
```

### Herramientas incluidas en CAINE

```
CAINE incluye:
├── forensic_suite (nuestra)
├── Autopsy (GUI de analisis)
├── Scalpel / Foremost (carving)
├── Volatility (memoria)
├── Sleuth Kit (filesystem)
├── Wireshark (red)
├── Hashdeep (hashing)
├── Guymager (clonado GUI)
└── Mas de 200 herramientas forenses
```

---

## FLUJO COMPLETO REAL

### Caso: Robo de informacion con USB

```
PASO 1: Llegar a la escena
├── Documentar fecha/hora
├── Fotografiar escena
├── Identificar dispositivos (forensic_suite listar)
└── No tocar nada aun

PASO 2: Preservar
├── Conectar write-blocker al USB
├── En TU laptop Linux:
│   sudo forensic_suite bloquear /dev/sdc
└── Verificar: sudo blockdev --getro /dev/sdc

PASO 3: Adquirir
├── Clonar USB:
│   sudo dcfldd if=/dev/sdc of=/evidencia/usb.raw bs=4M
├── Hash seguro:
│   forensic_suite hash /evidencia/usb.raw -g
├── Verificar integridad:
│   forensic_suite verificar /evidencia/usb.raw.hash
├── Si PC encendida: volcado memoria
│   sudo forensic_suite memoria --adquirir
└── Cadena de custodia:
    forensic_suite acta usb.raw --perito "Tu" --caso "X"

PASO 4: Transportar
├── Empaquetar evidencia
├── Sellar con cinta
├── Firmar sellos
└── Registrar en acta

PASO 5: Analizar (en laboratorio)
├── Trabajar SOLO sobre copia
├── Recuperar archivos:
│   forensic_suite carve usb.raw -p recuperacion -o out
├── Analizar memoria (si hay dump):
│   forensic_suite memoria --analizar --dump memoria.raw
└── Generar informe

PASO 6: Presentar
├── Informe pericial
├── Hashes de integridad
├── Firmas GPG
├── Sellos de tiempo
└── Cadena de custodia completa
```

---

## ERRORES COMUNES

### Error 1: "Ejecuto forensic_suite en Windows del sospechoso"
**Consecuencia:** Evidencia contaminada
**Solucion:** Nunca hacerlo. Usar USB Linux.

### Error 2: "No use write-blocker"
**Consecuencia:** Sin bloqueo hardware, la evidencia es cuestionable
**Solucion:** Siempre usar write-blocker fisico para tribunales

### Error 3: "Cloné con dd sin verificar bloqueo"
**Consecuencia:** Si el bloqueo fallo, el clon esta corrupto
**Solucion:** Verificar con `blockdev --getro` antes de clonar

### Error 4: "Hice todo en Windows"
**Consecuencia:** Las herramientas Linux no funcionan en Windows
**Solucion:** Bootear USB Linux o usar herramientas Windows nativas

---

**FIN**
