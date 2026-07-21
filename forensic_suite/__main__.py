#!/usr/bin/env python3
"""
ForensicSuite - Punto de entrada CLI
====================================
Uso:
    python -m forensic_suite hash /path/to/evidence.raw
    python -m forensic_suite bloquear /dev/sdb
    python -m forensic_suite acta --archivo evidence.raw --perito "Juan"
    python -m forensic_suite firmar evidence.raw --key ABC123
    python -m forensic_suite timestamp evidence.raw
    python -m forensic_suite verificar-timestamp evidence.raw.tsr
    python -m forensic_suite manifest /path/to/evidence/
    python -m forensic_suite daemon --status
    python -m forensic_suite interact --caso MP-001 --perito "Juan"
"""

import argparse
import json
import os
import sys
from datetime import datetime


def cmd_hash(args):
    from forensic_suite.core.hasher import ForensicHasher
    hasher = ForensicHasher()

    if os.path.isdir(args.archivo):
        print(f"Error: '{args.archivo}' es un directorio, no un archivo", file=sys.stderr)
        print("Use: forensic_suite manifest <directorio> para hashes de directorios", file=sys.stderr)
        return 1

    try:
        if args.algoritmo:
            if args.algoritmo == "sha256":
                h = hasher.calcular_sha256(args.archivo)
            elif args.algoritmo == "sha512":
                h = hasher.calcular_sha512(args.archivo)
            elif args.algoritmo == "md5":
                h = hasher.calcular_md5(args.archivo)
            else:
                print(f"Error: algoritmo '{args.algoritmo}' no valido", file=sys.stderr)
                return 1
            print(h)
        else:
            r = hasher.calcular_todos(args.archivo)
            print(f"Archivo:   {r.archivo}")
            print(f"Tamano:    {r.tamano_bytes} bytes")
            print(f"SHA-256:   {r.sha256}")
            print(f"SHA-512:   {r.sha512}")
            print(f"MD5:       {r.md5}")
            if args.generar_archivos:
                resultado = hasher.generar_archivo_hashes(args.archivo)
                print(f"\nArchivo hash: {resultado['ruta_hash']}")
                print("Estado: Solo lectura (protegido)")
                if "firma" in resultado["archivos"]:
                    print(f"Firma GPG: {resultado['archivos']['firma']}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_verificar(args):
    from forensic_suite.core.hasher import ForensicHasher
    hasher = ForensicHasher()

    # Si el archivo es .hash, verificar automaticamente
    if args.archivo.endswith(".hash"):
        resultado = hasher.verificar_archivo_hashes(args.archivo)

        if not resultado["exito"]:
            print(f"Error: {resultado['mensaje']}", file=sys.stderr)
            return 1

        print("VERIFICACION AUTOMATICA DE HASHES")
        print("=" * 50)
        print(f"Archivo original: {resultado['archivo_original']}")
        print(f"Fecha de firmado: {resultado['fecha_firma']}")
        print()

        print("COMPARACION DE HASHES:")
        for alg, valido in resultado["verificaciones"].items():
            esperado = resultado["hashes_esperados"].get(alg, "")[:16]
            actual = resultado["hashes_actuales"].get(alg, "")[:16]
            estado = "OK" if valido else "FALLO"
            print(f"  {alg.upper():<8} {estado:<8} {esperado}... = {actual}...")

        print()
        if resultado["firma_gpg"] is not None:
            estado_firma = "VALIDA" if resultado["firma_gpg"] else "INVALIDA"
            print(f"Firma GPG: {estado_firma}")

        print()
        print(f"RESULTADO: {resultado['mensaje']}")
        return 0 if resultado["todos_validos"] else 1

    # Si no es .hash, verificar con hash proporcionado
    if not args.hash:
        print("Error: se requiere un hash o un archivo .hash", file=sys.stderr)
        return 1

    r = hasher.verificar_hash(args.archivo, args.hash, args.algoritmo)
    if r["coincide"]:
        print(f"INTEGRIDAD VERIFICADA - {args.algoritmo.upper()}")
        print(f"  Hash: {r['hash_actual']}")
    else:
        print(f"INTEGRIDAD COMPROMETIDA", file=sys.stderr)
        print(f"  Esperado: {r['hash_esperado']}", file=sys.stderr)
        print(f"  Actual:   {r['hash_actual']}", file=sys.stderr)
    return 0 if r["coincide"] else 1


def cmd_bloquear(args):
    from forensic_suite.core.dispositivo import DispositivoForense, _obtener_ruta_raiz

    if os.geteuid() != 0:
        print("Error: se requiere root para bloquear dispositivos", file=sys.stderr)
        print("Ejecute: sudo forensic_suite bloquear /dev/sdX", file=sys.stderr)
        return 1

    raiz = _obtener_ruta_raiz()
    if args.dispositivo == raiz:
        print(f"ERROR DE SEGURIDAD: {args.dispositivo} es el disco desde el cual corre el sistema operativo actual.",
              file=sys.stderr)
        print("No se permite bloquear el disco de arranque.", file=sys.stderr)
        print("", file=sys.stderr)
        print("Si está analizando un equipo apagado, arranque desde un USB Live forense;", file=sys.stderr)
        print("desde allí el disco interno del anfitrión NO será el dispositivo raíz y podrá bloquearlo.", file=sys.stderr)
        return 1

    disp = DispositivoForense(args.dispositivo)
    try:
        disp.bloquear()
        print(f"Dispositivo {args.dispositivo} bloqueado correctamente")
        print(disp.verificar())
    except Exception as e:
        print(f"Error al bloquear: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_desbloquear(args):
    from forensic_suite.core.dispositivo import DispositivoForense

    if os.geteuid() != 0:
        print("Error: se requiere root", file=sys.stderr)
        return 1

    disp = DispositivoForense(args.dispositivo)
    try:
        disp.desmontar_y_liberar()
        print(f"Dispositivo {args.dispositivo} desbloqueado")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


def cmd_listar(args):
    from forensic_suite.core.dispositivo import identificar_dispositivos
    dispositivos = identificar_dispositivos(excluir_root=args.incluir_sistema)
    if not dispositivos:
        print("No se encontraron dispositivos de almacenamiento")
        return 0

    print()
    print("  DISPOSITIVOS DE ALMACENAMIENTO DETECTADOS")
    print("  " + "=" * 50)
    print()

    for d in dispositivos:
        ro = "BLOQUEADO (solo lectura)" if d.tipo in ["ssd", "hdd", "usb"] else d.tipo
        print(f"  Dispositivo:  /dev/{d.nombre}")
        print(f"  Modelo:       {d.modelo}")
        print(f"  Serial:       {d.serial}")
        print(f"  Tamano:       {d.tamaño}")
        print(f"  Tipo:         {d.tipo}")
        if d.montaje_actual:
            print(f"  Montado en:   {d.montaje_actual}")
        if d.particiones:
            print(f"  Particiones:  {len(d.particiones)}")
        print()

    print(f"  Total: {len(dispositivos)} dispositivo(s)")
    print()
    return 0


def cmd_acta(args):
    from forensic_suite.core.cadena_custodia import CadenaCustodia
    from forensic_suite.core.hasher import ForensicHasher

    hasher = ForensicHasher()
    try:
        hashes = hasher.calcular_todos(args.archivo)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    cadena = CadenaCustodia(
        archivo=os.path.basename(args.archivo),
        sha256=hashes.sha256,
        sha512=hashes.sha512,
        md5=hashes.md5,
        tamano=hashes.tamano_bytes,
        colector_nombre=args.perito or "",
        colector_cedula=args.cedula or "",
        colector_cargo=args.cargo or "",
        referencia=args.caso or ""
    )

    if args.transferir:
        for t in args.transferir:
            partes = t.split(":")
            if len(partes) == 3:
                cadena.agregar_transferencia(partes[0], partes[1], partes[2])

    if args.cerrar:
        cadena.cerrar_cadena(args.cerrar, args.autoridad or "")

    ruta = args.salida or args.archivo + ".chain"
    cadena.crear_acta(ruta)
    print(f"Acta generada: {ruta}")

    if args.json:
        ruta_json = ruta.replace(".chain", ".json")
        cadena.exportar_json(ruta_json)
        print(f"JSON exportado: {ruta_json}")

    return 0


def cmd_firmar(args):
    from forensic_suite.core.firma_gpg import ForensicGPG

    gpg = ForensicGPG(key_id=args.key)
    verif = gpg.verificar_gpg_instalado()
    if not verif["instalado"]:
        print("Error: GPG no instalado", file=sys.stderr)
        return 1

    resultado = gpg.firmar(args.archivo, args.salida)
    if resultado.exito:
        print(f"Firma generada: {resultado.archivo_firma}")
        print(f"Key ID: {resultado.key_id}")
    else:
        print(f"Error: {resultado.mensaje}", file=sys.stderr)
        return 1
    return 0


def cmd_verificar_firma(args):
    from forensic_suite.core.firma_gpg import ForensicGPG

    gpg = ForensicGPG()
    r = gpg.verificar(args.archivo, args.firma)
    print(r["mensaje"])
    if args.verbose and r.get("info"):
        print(r["info"])
    return 0 if r["verificado"] else 1


def cmd_claves(args):
    from forensic_suite.core.firma_gpg import ForensicGPG

    gpg = ForensicGPG()
    verif = gpg.verificar_gpg_instalado()
    if not verif["instalado"]:
        print("Error: GPG no instalado", file=sys.stderr)
        return 1

    claves = gpg.listar_claves()
    if not claves:
        print("No hay claves secretas disponibles")
        print("Genere una con: gpg --gen-key")
        return 0

    print(f"{'Key ID':<20} {'UID'}")
    print("-" * 60)
    for c in claves:
        print(f"{c['key_id']:<20} {c['uid']}")
    return 0


def cmd_timestamp(args):
    from forensic_suite.core.timestamp import ForensicTimestamp

    ts = ForensicTimestamp(tsa_server=args.tsa)
    resultado = ts.solicitar_timestamp(
        args.archivo,
        algoritmo=args.algoritmo or "sha256",
        ruta_token=args.token_salida
    )

    if resultado.exito:
        print(f"Timestamp RFC 3161 obtenido")
        print(f"  TSA:       {resultado.tsa}")
        print(f"  Fecha:     {resultado.fecha_timestamp}")
        print(f"  Hash:      {resultado.hash}")
        print(f"  Token:     {resultado.archivo_token}")
    else:
        print(f"Error: {resultado.mensaje}", file=sys.stderr)
        return 1
    return 0


def cmd_verificar_timestamp(args):
    from forensic_suite.core.timestamp import ForensicTimestamp

    ts = ForensicTimestamp()
    resultado = ts.verificar_timestamp(args.token)

    if resultado["valido"]:
        print(f"TIMESTAMP VALIDO")
        print(f"  Token: {args.token}")
        print(f"  Texto:")
        print(resultado["texto"])
    else:
        print(f"ERROR: {resultado['mensaje']}", file=sys.stderr)
        return 1
    return 0


def cmd_manifest(args):
    from forensic_suite.core.manifest import ForensicManifest
    import socket

    m = ForensicManifest()
    ruta = args.directorio

    if os.path.isfile(ruta):
        m.agregar_archivo(ruta)
    elif os.path.isdir(ruta):
        ext = args.extensiones.split(",") if args.extensiones else None
        excl = args.excluir.split(",") if args.excluir else None
        archivos = m.escanear_directorio(ruta, extensiones=ext, excluidos=excl)
        print(f"Escaneados: {len(archivos)} archivos")
    else:
        print(f"Error: '{ruta}' no es archivo ni directorio", file=sys.stderr)
        return 1

    manifest = m.generar_manifest(
        caso_id=args.caso or "",
        perito=args.perito or "",
        directorio_origen=ruta,
        host=socket.gethostname()
    )

    salida = args.salida or os.path.join(ruta if os.path.isdir(ruta) else os.path.dirname(ruta),
                                          "manifest.json")
    m.guardar(manifest, salida)
    print(f"Manifest generado: {salida}")
    print(f"  Archivos: {manifest.total_archivos}")
    print(f"  Tamano:   {manifest.total_bytes} bytes")
    print(f"  SHA-256:  {manifest.manifest_sha256[:32]}...")

    if args.verificar:
        verif = m.verificar(manifest)
        print(f"  Verificacion: {'OK' if verif['manifest_valido'] else 'FAIL'}")
    return 0


def cmd_verificar_manifest(args):
    from forensic_suite.core.manifest import ForensicManifest

    m = ForensicManifest()
    manifest = m.cargar(args.manifest)
    verif = m.verificar(manifest)

    print(f"Manifest: {args.manifest}")
    print(f"  Manifest SHA-256: {'VALIDO' if verif['integridad_manifest_256'] else 'INVALIDO'}")
    print(f"  Manifest SHA-512: {'VALIDO' if verif['integridad_manifest_512'] else 'INVALIDO'}")
    print(f"  Archivos OK:     {verif['archivos_verificados']}/{verif['total_archivos']}")
    print(f"  Archivos fallidos: {verif['archivos_fallidos']}")

    if verif["archivos_fallidos"] > 0:
        print("\n  Archivos con problemas:")
        for d in verif["detalles"]:
            if not d["integridad"]:
                print(f"    - {d['archivo']}: {d.get('error', 'hash no coincide')}")
    return 0 if verif["manifest_valido"] else 1


def cmd_perito(args):
    from forensic_suite.core.perito import PeritoConfig

    if args.ver:
        config = PeritoConfig.cargar()
        print(config)
        return 0

    if args.configurar:
        config = PeritoConfig.configurar_perito_interactivo()
        config.guardar()
        print("Configuracion guardada en ~/.forensic_suite/perito.conf")
        return 0

    if args.info:
        config = PeritoConfig()
        info = config.info_sistema()
        for k, v in info.items():
            print(f"  {k}: {v}")
        return 0

    print("Use: forensic_suite perito --configurar")
    print("    forensic_suite perito --ver")
    print("    forensic_suite perito --info")
    return 0


def cmd_daemon(args):
    from forensic_suite.daemon import forensic_blockerd as fb

    if args.accion == "status":
        import subprocess

        print()
        print("  ESTADO DEL SISTEMA FORENSE")
        print("  " + "=" * 40)
        print()

        # Verificar regla udev
        regla = "/etc/udev/rules.d/10-forensic-block.rules"
        import os
        if os.path.exists(regla):
            print(f"  Regla udev:    INSTALADA ({regla})")
            # Verificar si contiene el comando correcto
            with open(regla) as f:
                contenido = f.read()
                if "blockdev --setro" in contenido:
                    print("  Bloqueo:       blockdev --setro (configurado)")
                if "hdparm -r1" in contenido:
                    print("  Bloqueo:       hdparm -r1 (configurado)")
        else:
            print("  Regla udev:    NO INSTALADA")

        # Verificar si las reglas estan recargadas
        try:
            r = subprocess.run(["udevadm", "control", "--reload-rules"],
                             capture_output=True, timeout=5)
            if r.returncode == 0:
                print("  Reglas udev:   RECARGADAS")
            else:
                print("  Reglas udev:   Error recargando (ejecute: udevadm control --reload-rules)")
        except Exception:
            print("  Reglas udev:   No se pudo verificar")

        # Verificar herramientas
        for herramienta in ["/usr/sbin/blockdev", "/usr/sbin/hdparm"]:
            if os.path.exists(herramienta):
                print(f"  {os.path.basename(herramienta):15} INSTALADO")
            else:
                print(f"  {os.path.basename(herramienta):15} NO ENCONTRADO")

        # Verificar dispositivos bloqueados
        print()
        print("  DISPOSITIVOS CONECTADOS:")
        try:
            r = subprocess.run(["lsblk", "-o", "NAME,SIZE,RO,RM,MODEL"],
                             capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                for linea in r.stdout.strip().split("\n"):
                    print(f"    {linea}")
        except Exception:
            print("    Error listando dispositivos")

        print()
        print("  NOTA: La regla udev se ejecuta al conectar un disco nuevo.")
        print("  Para el disco actual, ejecute:")
        print("    sudo forensic_suite bloquear /dev/sdX")
        print()
        return 0

    if not fb.es_root():
        print("Error: se requiere root para instalar/desinstalar el daemon")
        print("Ejecute: sudo forensic_suite daemon install")
        return 1

    if args.accion == "install":
        print("Instalando regla udev de bloqueo forense...")
        resultado = fb.instalar_regla_udev()
        if resultado.get("ok", False):
            print("Regla udev instalada en /etc/udev/rules.d/10-forensic-block.rules")
            print("Se ejecuta automaticamente al conectar un nuevo dispositivo")
        else:
            print(f"Error: {resultado.get('error', 'desconocido')}")
            return 1
        return 0

    if args.accion == "uninstall":
        print("Desinstalando daemon...")
        resultado = fb.desinstalar_daemon()
        if resultado.get("ok", False):
            print("Daemon desinstalado correctamente")
        else:
            print(f"Error: {resultado.get('error', 'desconocido')}")
            return 1
        return 0

    return 0


def cmd_carve(args):
    from forensic_suite.core.scalpel import ForensicScalpel, PERFILES

    if args.perfiles:
        perfiles = ForensicScalpel.listar_perfiles()
        descripciones = {
            "recuperacion": "Archivos eliminados, particiones perdidas, datos residuales",
            "medios": "Fotos, videos, audio, evidencia multimedia",
            "documentos": "Ofimatica, textos, correos, formularios",
            "redes": "Capturas de red, logs de firewall, trafico",
            "cripto": "Claves, certificados, tokens, credenciales",
            "mensajeria": "Bases SQLite, imagenes y documentos de apps de mensajeria (WhatsApp, Telegram, Signal)",
            "general": "Configuracion general, 39 tipos comunes"
        }
        print("PERFILES DISPONIBLES:")
        print(f"{'Perfil':<15} {'Tipos':<8} {'Descripcion'}")
        print("-" * 75)
        for nombre, info in perfiles.items():
            desc = descripciones.get(nombre, "")
            print(f"{nombre:<15} {info['tipos_configurados']:<8} {desc}")
        print()
        print("Uso: forensic_suite carve <fuente> -c <perfil>")
        print("     forensic_suite carve /dev/sdc1 -p cripto -o /tmp/recuperados")
        return 0

    config = args.config
    perfil = args.perfil
    if perfil:
        try:
            scalpel = ForensicScalpel(perfil=perfil)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    elif not config:
        config = os.path.join(os.path.dirname(__file__), "daemon", "scalpel_forense.conf")
        scalpel = ForensicScalpel(config_file=config)
    else:
        scalpel = ForensicScalpel(config_file=config)

    if args.verificar_instalacion:
        verif = scalpel.verificar_instalacion()
        print(f"Scalpel:    {'INSTALADO' if verif['instalado'] else 'NO INSTALADO'}")
        print(f"Version:    {verif.get('version', '?')}")
        print(f"Config:     {verif.get('config', '?')}")
        print(f"Estado:     {verif.get('mensaje', '?')}")
        return 0 if verif["instalado"] else 1

    if args.listar_tipos:
        tipos = scalpel.listar_tipos()
        print(f"Tipos de archivo configurados: {len(tipos)}")
        print(f"{'Extension':<12} {'Max Tamano':<15} {'Header'}")
        print("-" * 60)
        for t in tipos[:30]:
            print(f"{t['extension']:<12} {t['max_size']:<15} {t['header'][:30]}")
        if len(tipos) > 30:
            print(f"  ... y {len(tipos) - 30} mas")
        return 0

    if not args.fuente:
        print("Error: se requiere una fuente (dispositivo o imagen)", file=sys.stderr)
        return 1

    salida = args.salida or args.fuente + "_carved"

    print(f"Fuente:     {args.fuente}")
    print(f"Salida:     {salida}")
    print(f"Ejecutando scalpel...")

    resultado = scalpel.ejecutar_carving(
        fuente=args.fuente,
        directorio_salida=salida,
        verbose=args.verbose
    )

    if not resultado.exito:
        print(f"Error: {resultado.mensaje}", file=sys.stderr)
        return 1

    print()
    print(f"  ARCHIVOS RECUPERADOS: {resultado.total_archivos}")
    print(f"  Tamano total:        {resultado.tamano_total} bytes")
    print(f"  Tiempo:              {resultado.tiempo_segundos:.1f}s")
    print()

    if resultado.tipos_encontrados:
        print("  POR TIPO:")
        for tipo, count in sorted(resultado.tipos_encontrados.items()):
            print(f"    .{tipo:<10} {count} archivo(s)")
        print()

    if resultado.archivos_recuperados:
        print("  ARCHIVOS:")
        for a in resultado.archivos_recuperados[:20]:
            print(f"    {a['nombre']:<30} {a['tamano']:>10} bytes  {a['sha256'][:16]}...")
        if len(resultado.archivos_recuperados) > 20:
            print(f"    ... y {len(resultado.archivos_recuperados) - 20} mas")
        print()

    if args.manifest:
        print("Generando manifest de carving...")
        manifest = scalpel.generar_manifest_carving(
            directorio_salida=salida,
            caso_id=args.caso or "",
            perito=args.perito or ""
        )
        if "error" not in manifest:
            print(f"  Manifest: {salida}/carving_manifest.json")
            print(f"  SHA-256:  {manifest.get('manifest_sha256', '?')[:32]}...")

    print()
    print(f"Archivos recuperados en: {salida}")
    return 0


def cmd_analyze(args):
    from forensic_suite.core.scalpel import ForensicScalpel

    scalpel = ForensicScalpel()
    stats = scalpel.analizar_audit(args.directorio)

    if "error" in stats:
        print(f"Error: {stats['error']}", file=sys.stderr)
        return 1

    print(f"Analisis de audit.txt:")
    print(f"  Tipos encontrados: {stats['total']}")
    for linea in stats.get("lineas_importantes", []):
        print(f"  {linea}")
    return 0


def cmd_memoria(args):
    from forensic_suite.core.memoria import ForensicMemoria

    memoria = ForensicMemoria()

    if args.verificar_entorno:
        entorno = memoria.verificar_entorno()
        print()
        print("  ENTORNO DE MEMORIA FORENSE")
        print("  " + "=" * 40)
        print(f"  mforense:    {'OK' if entorno['mforense'] else 'NO INSTALADO'}")
        print(f"  Root:        {'SI' if entorno['root'] else 'NO (requiere sudo)'}")
        print(f"  LiME:        {'DISPONIBLE' if entorno['lime'] else 'NO DISPONIBLE'}")
        print(f"  AVML:        {'DISPONIBLE' if entorno['avml'] else 'NO DISPONIBLE'}")
        print(f"  Volatility:  {'DISPONIBLE' if entorno['volatility'] else 'NO DISPONIBLE'}")
        print()
        return 0 if entorno["mforense"] else 1

    if args.adquirir:
        print("ADQUIRIENDO MEMORIA VOLATIL...")
        print("  Esto puede tardar varios minutos dependiendo de la RAM")
        print()
        resultado = memoria.adquirir_memoria(
            caso=args.caso or "",
            directorio=args.directorio or "."
        )
        if resultado["exito"]:
            print(resultado["salida"])
        else:
            print(f"Error: {resultado['error']}", file=sys.stderr)
            return 1
        return 0

    if args.analizar:
        if not args.dump:
            print("Error: se requiere --dump <archivo_raw>", file=sys.stderr)
            return 1
        print(f"Analizando {args.dump} con plugin {args.plugin}...")
        resultado = memoria.analizar_memoria(
            dump_file=args.dump,
            plugin=args.plugin
        )
        if resultado["exito"]:
            print(resultado["salida"])
        else:
            print(f"Error: {resultado['error']}", file=sys.stderr)
            return 1
        return 0

    if args.verificar:
        if not args.dump:
            print("Error: se requiere --dump <archivo_raw>", file=sys.stderr)
            return 1
        print(f"Verificando integridad de {args.dump}...")
        resultado = memoria.verificar_integridad(args.dump)
        if resultado["exito"]:
            print(resultado["salida"])
        else:
            print(f"Error: {resultado['error']}", file=sys.stderr)
            return 1
        return 0

    if args.estado:
        resultado = memoria.estado_caso()
        if resultado["exito"]:
            print(resultado["salida"])
        else:
            print(f"Error: {resultado['error']}", file=sys.stderr)
            return 1
        return 0

    if args.cadena:
        resultado = memoria.cadena_custodia()
        if resultado["exito"]:
            print(resultado["salida"])
        else:
            print(f"Error: {resultado['error']}", file=sys.stderr)
            return 1
        return 0

    if args.cifrar:
        resultado = memoria.cifrar_evidencia(args.cifrar)
        if resultado["exito"]:
            print(resultado["salida"])
        else:
            print(f"Error: {resultado['error']}", file=sys.stderr)
            return 1
        return 0

    if args.firmar:
        resultado = memoria.firmar_cadena(args.firmar)
        if resultado["exito"]:
            print(resultado["salida"])
        else:
            print(f"Error: {resultado['error']}", file=sys.stderr)
            return 1
        return 0

    if args.informe:
        resultado = memoria.generar_informe()
        if resultado["exito"]:
            print(resultado["salida"])
        else:
            print(f"Error: {resultado['error']}", file=sys.stderr)
            return 1
        return 0

    print("Uso: forensic_suite memoria --adquirir")
    print("     forensic_suite memoria --analizar --dump <raw> --plugin <plugin>")
    print("     forensic_suite memoria --verificar --dump <raw>")
    print("     forensic_suite memoria --verificar-entorno")
    return 0


def cmd_interact(args):
    """Inicia el modo interactivo (framework)"""
    from forensic_suite.shell import ForensicShell
    
    shell = ForensicShell()
    
    # Configurar si se proporcionaron argumentos
    if args.caso:
        shell.case_id = args.caso
    if args.perito:
        shell.perito_name = args.perito
    if args.directorio:
        shell.current_dir = os.path.abspath(args.directorio)
    
    shell.ejecutar()
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="forensic_suite",
        description="ForensicSuite - Framework de Analisis Forense Digital",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s hash evidence.raw                      # Hashes SHA-256/SHA-512/MD5
  %(prog)s hash evidence.raw -a sha256            # Solo SHA-256
  %(prog)s verificar evidence.raw HASH_ABC...     # Verificar integridad
  %(prog)s bloquear /dev/sdb                      # Bloquear escritura (root)
  %(prog)s listar                                 # Listar dispositivos
  %(prog)s acta evidence.raw --perito "Juan"      # Generar acta de custodia
  %(prog)s firmar evidence.raw --key ABC123       # Firma GPG detached
  %(prog)s timestamp evidence.raw                 # Sello de tiempo RFC 3161
  %(prog)s verificar-timestamp evidence.raw.tsr   # Verificar sello de tiempo
  %(prog)s manifest /path/to/evidence/            # Manifest JSON canonicos
  %(prog)s verificar-manifest manifest.json       # Verificar manifest
  %(prog)s perito --configurar                    # Configurar perito
  %(prog)s daemon status                          # Estado del daemon
  %(prog)s interact                               # Modo interactivo (framework)
  %(prog)s interact --caso MP-001 --perito "Juan" # Modo interactivo con caso
"""
    )
    from forensic_suite import __version__
    parser.add_argument("--version", action="version", version=f"ForensicSuite {__version__}")

    sub = parser.add_subparsers(dest="comando", help="Comandos disponibles")

    # hash
    p_hash = sub.add_parser("hash", help="Calcular hashes criptograficos")
    p_hash.add_argument("archivo", help="Ruta del archivo")
    p_hash.add_argument("-a", "--algoritmo", choices=["sha256", "sha512", "md5"],
                        help="Algoritmo especifico (default: todos)")
    p_hash.add_argument("-g", "--generar-archivos", action="store_true",
                        help="Generar archivos .sha256/.sha512/.md5")

    # verificar
    p_verif = sub.add_parser("verificar", help="Verificar hash de un archivo o archivo .hash")
    p_verif.add_argument("archivo", help="Ruta del archivo o archivo .hash")
    p_verif.add_argument("hash", nargs="?", help="Hash esperado (si no se provee, busca archivo .hash)")
    p_verif.add_argument("-a", "--algoritmo", default="sha256",
                         choices=["sha256", "sha512", "md5"])

    # bloquear
    p_block = sub.add_parser("bloquear", help="Bloquear escritura de dispositivo (root)")
    p_block.add_argument("dispositivo", help="Ruta del dispositivo (ej: /dev/sdb)")

    # desbloquear
    p_unblock = sub.add_parser("desbloquear", help="Desbloquear dispositivo (root)")
    p_unblock.add_argument("dispositivo", help="Ruta del dispositivo")

    # listar
    p_list = sub.add_parser("listar", help="Listar dispositivos de almacenamiento")
    p_list.add_argument("-s", "--incluir-sistema", action="store_true",
                        help="Incluir disco del sistema")

    # acta
    p_acta = sub.add_parser("acta", help="Generar acta de cadena de custodia MP 2017")
    p_acta.add_argument("archivo", help="Archivo de evidencia")
    p_acta.add_argument("--perito", help="Nombre del perito")
    p_acta.add_argument("--cedula", help="Cedula del perito")
    p_acta.add_argument("--cargo", help="Cargo del perito")
    p_acta.add_argument("--caso", help="Numero de caso/referencia")
    p_acta.add_argument("-t", "--transferir", action="append",
                        help="Transferencia (origen:destino:motivo)")
    p_acta.add_argument("--cerrar", help="Cerrar cadena (disposicion)")
    p_acta.add_argument("--autoridad", help="Autoridad que autoriza cierre")
    p_acta.add_argument("-o", "--salida", help="Ruta de salida")
    p_acta.add_argument("--json", action="store_true", help="Exportar JSON tambien")

    # firmar
    p_firmar = sub.add_parser("firmar", help="Firmar archivo con GPG")
    p_firmar.add_argument("archivo", help="Archivo a firmar")
    p_firmar.add_argument("--key", help="Key ID GPG")
    p_firmar.add_argument("-o", "--salida", help="Ruta de la firma")

    # verificar-firma
    p_vf = sub.add_parser("verificar-firma", help="Verificar firma GPG")
    p_vf.add_argument("archivo", help="Archivo original")
    p_vf.add_argument("--firma", help="Ruta de la firma (.asc)")
    p_vf.add_argument("-v", "--verbose", action="store_true")

    # claves
    sub.add_parser("claves", help="Listar claves GPG secretas")

    # timestamp
    p_ts = sub.add_parser("timestamp", help="Obtener sello de tiempo RFC 3161")
    p_ts.add_argument("archivo", help="Archivo a timestampar")
    p_ts.add_argument("--tsa", help="Servidor TSA preferido")
    p_ts.add_argument("-a", "--algoritmo", default="sha256")
    p_ts.add_argument("-o", "--token-salida", help="Ruta del token TSA")

    # verificar-timestamp
    p_vts = sub.add_parser("verificar-timestamp", help="Verificar token TSA RFC 3161")
    p_vts.add_argument("token", help="Ruta del token TSA (.tsr)")

    # manifest
    p_man = sub.add_parser("manifest", help="Generar manifest JSON canonico")
    p_man.add_argument("directorio", help="Directorio o archivo a manifestar")
    p_man.add_argument("--caso", help="ID del caso")
    p_man.add_argument("--perito", help="Nombre del perito")
    p_man.add_argument("-o", "--salida", help="Ruta de salida")
    p_man.add_argument("-e", "--extensiones", help="Extensiones a incluir (csv)")
    p_man.add_argument("-x", "--excluir", help="Patrones a excluir (csv)")
    p_man.add_argument("-v", "--verificar", action="store_true",
                        help="Verificar manifest despues de generar")

    # verificar-manifest
    p_vm = sub.add_parser("verificar-manifest", help="Verificar manifest JSON")
    p_vm.add_argument("manifest", help="Ruta del manifest.json")

    # carve
    p_carve = sub.add_parser("carve", help="Recuperar archivos eliminados (Scalpel)")
    p_carve.add_argument("fuente", nargs="?", help="Dispositivo o imagen (ej: /dev/sdc1, evidencia.raw)")
    p_carve.add_argument("-o", "--salida", help="Directorio de salida")
    p_carve.add_argument("--caso", help="ID del caso")
    p_carve.add_argument("--perito", help="Nombre del perito")
    p_carve.add_argument("-c", "--config", help="Archivo de configuracion scalpel")
    p_carve.add_argument("-p", "--perfil", choices=["recuperacion", "medios", "documentos", "redes", "cripto", "mensajeria", "general"],
                         help="Perfil de configuracion especializado")
    p_carve.add_argument("--perfiles", action="store_true",
                         help="Listar perfiles de configuracion disponibles")
    p_carve.add_argument("-m", "--manifest", action="store_true",
                         help="Generar manifest de carving")
    p_carve.add_argument("-v", "--verbose", action="store_true")
    p_carve.add_argument("--verificar-instalacion", action="store_true",
                         help="Verificar que scalpel esta instalado")
    p_carve.add_argument("--listar-tipos", action="store_true",
                         help="Listar tipos de archivo configurados")

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analizar resultados de scalpel")
    p_analyze.add_argument("directorio", help="Directorio de salida de scalpel")

    # memoria
    p_mem = sub.add_parser("memoria", help="Adquisicion y analisis de memoria volatil (mforense)")
    p_mem.add_argument("--verificar-entorno", action="store_true",
                       help="Verificar LiME/AVML/Volatility")
    p_mem.add_argument("--adquirir", action="store_true",
                       help="Adquirir dump de memoria RAM")
    p_mem.add_argument("--analizar", action="store_true",
                       help="Analizar dump con Volatility")
    p_mem.add_argument("--verificar", action="store_true",
                       help="Verificar integridad del dump")
    p_mem.add_argument("--dump", help="Ruta del dump de memoria (.raw)")
    p_mem.add_argument("--plugin", default="windows.pslist",
                       help="Plugin de Volatility (default: windows.pslist)")
    p_mem.add_argument("--caso", help="ID del caso")
    p_mem.add_argument("--directorio", help="Directorio de trabajo")
    p_mem.add_argument("--estado", action="store_true",
                       help="Ver estado del caso")
    p_mem.add_argument("--cadena", action="store_true",
                       help="Ver cadena de custodia")
    p_mem.add_argument("--cifrar", help="Cifrar archivo de evidencia")
    p_mem.add_argument("--firmar", help="Firmar cadena de custodia")
    p_mem.add_argument("--informe", action="store_true",
                       help="Generar informe pericial")

    # perito
    p_perito = sub.add_parser("perito", help="Configuracion del perito")
    p_perito.add_argument("--configurar", action="store_true",
                          help="Configurar perito interactivamente")
    p_perito.add_argument("--ver", action="store_true", help="Ver configuracion")
    p_perito.add_argument("--info", action="store_true", help="Info del sistema")

    # daemon
    p_daemon = sub.add_parser("daemon", help="Daemon de bloqueo automatico")
    p_daemon.add_argument("accion", choices=["status", "install", "uninstall"],
                          help="Accion a realizar")

    # interact (modo framework)
    p_interact = sub.add_parser("interact", help="Iniciar modo interactivo (framework)")
    p_interact.add_argument("--caso", help="ID del caso a trabajar")
    p_interact.add_argument("--perito", help="Nombre del perito")
    p_interact.add_argument("--directorio", help="Directorio de trabajo")

    args = parser.parse_args()

    if not args.comando:
        parser.print_help()
        return 0

    cmds = {
        "hash": cmd_hash,
        "verificar": cmd_verificar,
        "bloquear": cmd_bloquear,
        "desbloquear": cmd_desbloquear,
        "listar": cmd_listar,
        "acta": cmd_acta,
        "firmar": cmd_firmar,
        "verificar-firma": cmd_verificar_firma,
        "claves": cmd_claves,
        "timestamp": cmd_timestamp,
        "verificar-timestamp": cmd_verificar_timestamp,
        "manifest": cmd_manifest,
        "verificar-manifest": cmd_verificar_manifest,
        "perito": cmd_perito,
        "daemon": cmd_daemon,
        "carve": cmd_carve,
        "analyze": cmd_analyze,
        "memoria": cmd_memoria,
        "interact": cmd_interact,
    }

    handler = cmds.get(args.comando)
    if handler:
        return handler(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
