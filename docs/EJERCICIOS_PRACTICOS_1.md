# GUIA PRACTICA DE EJERCICIOS
# Practica Real con y sin Forensic Suite

**Objetivo:** Aprender haciendo
**Nivel:** Principiante a Intermedio
**Tiempo estimado:** 2-4 horas por ejercicio

---

## PREPARACION

```bash
# Crear entorno de practica
mkdir -p ~/forense_practica/{evidencia,clones,recuperados}

# Verificar que funciona
forensic_suite --help
```

---

## EJERCICIO 1: HASHING (15 min)

**Objetivo:** Aprender a calcular y verificar hashes

### Paso 1: Crear archivo
```bash
echo "Documento confidencial" > ~/forense_practica/secreto.txt
cat ~/forense_practica/secreto.txt
```

### Paso 2: Hash seguro CON la suite
```bash
forensic_suite hash ~/forense_practica/secreto.txt -g
```
**Se genero archivo .hash?** SI / NO
**Permisos del .hash:** ___

### Paso 3: Hash SIN la suite
```bash
sha256sum ~/forense_practica/secreto.txt
sha512sum ~/forense_practica/secreto.txt
md5sum ~/forense_practica/secreto.txt
```
**Son iguales los hashes?** SI / NO

### Paso 4: Modificar el archivo
```bash
echo "X" >> ~/forense_practica/secreto.txt
```

### Paso 5: Recalcular hash
```bash
forensic_suite hash ~/forense_practica/secreto.txt -g
```
**Los hashes cambiaron?** SI / NO
**El archivo .hash se actualizo?** SI / NO

### Paso 6: Verificar con el archivo .hash
```bash
forensic_suite verificar ~/forense_practica/secreto.txt.hash
```
**Resultado:** VERIFICADA / COMPROMETIDA

---

## EJERCICIO 2: LISTAR DISPOSITIVOS (10 min)

**Objetivo:** Identificar dispositivos conectados

### Paso 1: Conectar USB
```
Conecta un USB a tu computadora
```

### Paso 2: Listar CON la suite
```bash
forensic_suite listar
```
**Cual es el USB?** /dev/___

### Paso 3: Listar SIN la suite
```bash
lsblk -o NAME,SIZE,TYPE,MODEL
```
**La info es igual?** SI / NO

---

## EJERCICIO 3: BLOQUEO DE ESCRITURA (20 min)

**Objetivo:** Bloquear y verificar

### Paso 1: Estado actual
```bash
sudo blockdev --getro /dev/sdX
```
**Estado:** Bloqueado / No bloqueado

### Paso 2: Bloquear CON la suite
```bash
sudo forensic_suite bloquear /dev/sdX
```

### Paso 3: Verificar
```bash
forensic_suite listar
```
**Aparece BLOQUEADO?** SI / NO

### Paso 4: Bloquear SIN la suite
```bash
sudo blockdev --setro 1 /dev/sdX
sudo blockdev --getro /dev/sdX
```

### Paso 5: Probar
```bash
sudo touch /dev/sdX
```
**Resultado:** Read-only / Exito (ERROR)

### Paso 6: Desbloquear
```bash
sudo forensic_suite desbloquear /dev/sdX
```

---

## EJERCICIO 4: CLONADO (30 min)

**Objetivo:** Clonar dispositivo bit a bit

### Paso 1: Preparar USB
```bash
touch /media/tu_usuario/USB/archivo1.txt
echo "Datos" > /media/tu_usuario/USB/doc.txt
mkdir /media/tu_usuario/USB/secreto
echo "Secreto" > /media/tu_usuario/USB/secreto/oculto.txt
sudo umount /media/tu_usuario/USB
```

### Paso 2: Bloquear
```bash
sudo forensic_suite bloquear /dev/sdX
```

### Paso 3: Clonar CON la suite
```bash
sudo dcfldd if=/dev/sdX of=~/forense_practica/clones/usb.raw bs=4M hash=sha256
```
**Guarda el hash:** _______________

### Paso 4: Clonar SIN la suite
```bash
sudo forensic_suite desbloquear /dev/sdX
sudo dd if=/dev/sdX of=~/forense_practica/clones/usb_dd.raw bs=4M status=progress
```
**Mismo tamano?** SI / NO

### Paso 5: Trabajar con el clon
```bash
sudo mkdir -p /mnt/clon
sudo mount -o loop,ro ~/forense_practica/clones/usb.raw /mnt/clon
ls -la /mnt/clon/
```
**Ves los archivos?** SI / NO
