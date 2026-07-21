#!/usr/bin/env python3
"""
ForensicSuite - Punto de entrada CLI para Windows
=================================================

Version SEPARADA del CLI de Linux. Reutiliza los modulos core
que no dependen de herramientas del sistema Linux.

Comandos disponibles en Windows:
    hash, verificar, manifest, verificar-manifest,
    acta, firmar, verificar-firma, claves,
    timestamp, verificar-timestamp,
    perito, interact, carve, analyze,
    memoria (verificar/analizar con Volatility3),
    bloquear/desbloquear (politica USB global),
    listar (via PowerShell/WMI),
    daemon (no disponible en Windows)

Autor: Tr3w01
Version: 1.0.0
"""

import argparse
import os
import subprocess
import sys


# Reutilizar comandos comunes de la version Linux
from forensic_suite import __main__ as linux_main


def _cmd_no_disponible_windows(nombre: str):
    def _cmd(args):
        print(f"Comando '{nombre}' no disponible en Windows.")
        print("Windows no utiliza udev/systemd. Para proteccion USB real en Windows:")
        print("  1. Use write blockers de hardware")
        print("  2. Arranque el equipo con el USB Live forense")
        return 1
    return _cmd


def cmd_bloquear(args):
    from forensic_suite_windows.core import plataforma

    print("[Windows] Bloqueo de dispositivos no es equivalente a Linux.")
    print("Se intentara activar proteccion contra escritura USB global del sistema.")
    print("Esta operacion requiere reinicio para surtir efecto.")
    print()
    resultado = plataforma.bloquear_posible_windows(args.dispositivo)
    if resultado["ok"]:
        print("Proteccion contra escritura USB activada.")
        if resultado.get("advertencia"):
            print(f"Aviso: {resultado['advertencia']}")
        return 0
    else:
        print(f"Error: {resultado.get('error', 'No se pudo activar proteccion')}", file=sys.stderr)
        return 1


def cmd_desbloquear(args):
    from forensic_suite_windows.core import plataforma

    print("[Windows] Desactivando proteccion contra escritura USB global del sistema.")
    resultado = plataforma.desbloquear_posible_windows(args.dispositivo)
    if resultado["ok"]:
        print("Proteccion contra escritura USB desactivada.")
        if resultado.get("advertencia"):
            print(f"Aviso: {resultado['advertencia']}")
        return 0
    else:
        print(f"Error: {resultado.get('error', 'No se pudo desactivar proteccion')}", file=sys.stderr)
        return 1


def cmd_listar(args):
    from forensic_suite_windows.core import plataforma

    dispositivos = plataforma.listar_dispositivos()
    if not dispositivos:
        print("No se encontraron dispositivos de almacenamiento")
        return 0

    print()
    print("  DISPOSITIVOS DE ALMACENAMIENTO DETECTADOS (Windows)")
    print("  " + "=" * 50)
    print()

    for d in dispositivos:
        print(f"  Dispositivo:  {d.get('source', d.get('name'))}")
        print(f"  Modelo:       {d.get('model', 'Desconocido')}")
        print(f"  Serial:       {d.get('serial', '')}")
        print(f"  Tamano:       {d.get('size', 0)} bytes")
        print(f"  Tipo:         {d.get('type', 'disk')}")
        print()

    print(f"  Total: {len(dispositivos)} dispositivo(s)")
    print()
    print("  NOTA: En Windows no se puede bloquear dispositivos como en Linux.")
    print("        Use herramientas de hardware o arranque desde USB Live para bloqueo real.")
    print()
    return 0


def _detectar_volatility():
    for comando in ["volatility3", "vol", "vol.py"]:
        try:
            r = subprocess.run([comando, "--help"], capture_output=True, timeout=5)
            if r.returncode == 0:
                return comando
        except Exception:
            continue
    return None


def _detectar_winpmem_dumpit():
    herramientas = {
        "winpmem.exe": "winpmem",
        "winpmem_mini_x64.exe": "winpmem",
        "DumpIt.exe": "dumpit",
        "DumpIt64.exe": "dumpit",
    }
    encontradas = {"winpmem": False, "dumpit": False}
    for binario, clave in herramientas.items():
        try:
            subprocess.run([binario, "--help"], capture_output=True, timeout=5)
            encontradas[clave] = True
        except Exception:
            pass
    return encontradas


def cmd_memoria(args):
    if args.verificar_entorno:
        print()
        print("  ENTORNO DE MEMORIA FORENSE (Windows)")
        print("  " + "=" * 40)

        volatility_ok = _detectar_volatility() is not None
        herramientas = _detectar_winpmem_dumpit()

        print(f"  WinPmem:     {'DISPONIBLE' if herramientas['winpmem'] else 'NO DISPONIBLE'}")
        print(f"  DumpIt:      {'DISPONIBLE' if herramientas['dumpit'] else 'NO DISPONIBLE'}")
        print(f"  Volatility:  {'DISPONIBLE' if volatility_ok else 'NO DISPONIBLE'}")
        print()
        print("  NOTA: En Windows la adquisicion de memoria requiere")
        print("        winpmem.exe o DumpIt.exe en el PATH.")
        print()
        return 0 if (herramientas["winpmem"] or herramientas["dumpit"] or volatility_ok) else 1

    if args.adquirir:
        print("[Windows] La adquisicion de memoria RAM en Windows requiere herramientas externas.")
        print("Opciones soportadas si estan en el PATH:")
        print("  - winpmem.exe")
        print("  - DumpIt.exe")
        print("Ejecute la herramienta manualmente para generar el dump y luego:")
        print("  forensic_suite memoria --analizar --dump memoria.raw")
        return 1

    if args.analizar:
        if not args.dump:
            print("Error: se requiere --dump <archivo_raw>", file=sys.stderr)
            return 1

        vol_cmd = _detectar_volatility()
        if not vol_cmd:
            print("Error: Volatility3 no encontrado. Instale con: pip install volatility3", file=sys.stderr)
            return 1

        plugin = args.plugin or "windows.pslist"
        print(f"Analizando {args.dump} con plugin {plugin}...")
        try:
            r = subprocess.run([vol_cmd, "-f", args.dump, plugin],
                             capture_output=True, text=True, timeout=1800)
            print(r.stdout)
            if r.returncode != 0 and r.stderr:
                print(r.stderr, file=sys.stderr)
            return 0 if r.returncode == 0 else 1
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    if args.verificar:
        if not args.dump:
            print("Error: se requiere --dump <archivo_raw>", file=sys.stderr)
            return 1
        print("Verificacion de integridad de dumps no implementada en Windows.")
        print("Use Volatility3 manualmente para validar el dump.")
        return 1

    if args.estado or args.cadena or args.cifrar or args.firmar or args.informe:
        print("Estas opciones de memoria requieren mforense, disponible solo en Linux.")
        return 1

    return 0


def _configurar_parsers(sub):
    # hash
    p_hash = sub.add_parser("hash", help="Calcular hashes criptograficos")
    p_hash.add_argument("archivo", help="Archivo a hashear")
    p_hash.add_argument("-a", "--algoritmo", choices=["sha256", "sha512", "md5"],
                        help="Solo un algoritmo")
    p_hash.add_argument("-g", "--generar-archivos", action="store_true",
                        help="Generar archivos .sha256/.sha512/.md5/.hash")
    p_hash.set_defaults(func=linux_main.cmd_hash)

    # verificar
    p_ver = sub.add_parser("verificar", help="Verificar hash de un archivo")
    p_ver.add_argument("archivo", help="Archivo a verificar")
    p_ver.add_argument("--hash", help="Hash esperado")
    p_ver.add_argument("-a", "--algoritmo", default="sha256",
                       choices=["sha256", "sha512", "md5"])
    p_ver.set_defaults(func=linux_main.cmd_verificar)

    # acta
    p_acta = sub.add_parser("acta", help="Generar acta de cadena de custodia")
    p_acta.add_argument("archivo", help="Archivo de evidencia")
    p_acta.add_argument("--perito", help="Nombre del perito")
    p_acta.add_argument("--cedula", help="Cedula del perito")
    p_acta.add_argument("--cargo", help="Cargo del perito")
    p_acta.add_argument("--caso", help="Numero de caso")
    p_acta.add_argument("-t", "--transferir", action="append",
                        help="Transferencia (origen:destino:motivo)")
    p_acta.add_argument("--cerrar", help="Cerrar cadena")
    p_acta.add_argument("--autoridad", help="Autoridad que cierra")
    p_acta.add_argument("-o", "--salida", help="Ruta de salida")
    p_acta.add_argument("--json", action="store_true", help="Exportar JSON")
    p_acta.set_defaults(func=linux_main.cmd_acta)

    # firmar
    p_fir = sub.add_parser("firmar", help="Firmar archivo con GPG")
    p_fir.add_argument("archivo", help="Archivo a firmar")
    p_fir.add_argument("--key", help="Key ID GPG")
    p_fir.add_argument("-o", "--salida", help="Ruta de salida")
    p_fir.set_defaults(func=linux_main.cmd_firmar)

    # verificar-firma
    p_vf = sub.add_parser("verificar-firma", help="Verificar firma GPG")
    p_vf.add_argument("archivo", help="Archivo original")
    p_vf.add_argument("--firma", help="Ruta de firma")
    p_vf.add_argument("-v", "--verbose", action="store_true")
    p_vf.set_defaults(func=linux_main.cmd_verificar_firma)

    # claves
    p_claves = sub.add_parser("claves", help="Listar claves GPG")
    p_claves.set_defaults(func=linux_main.cmd_claves)

    # timestamp
    p_ts = sub.add_parser("timestamp", help="Obtener sello de tiempo RFC 3161")
    p_ts.add_argument("archivo", help="Archivo a timestampar")
    p_ts.add_argument("--tsa", help="Servidor TSA")
    p_ts.add_argument("-a", "--algoritmo", default="sha256")
    p_ts.add_argument("-o", "--token-salida", help="Ruta del token")
    p_ts.set_defaults(func=linux_main.cmd_timestamp)

    # verificar-timestamp
    p_vts = sub.add_parser("verificar-timestamp", help="Verificar token TSA")
    p_vts.add_argument("token", help="Ruta del token .tsr")
    p_vts.set_defaults(func=linux_main.cmd_verificar_timestamp)

    # manifest
    p_man = sub.add_parser("manifest", help="Generar manifest JSON")
    p_man.add_argument("directorio", help="Directorio o archivo")
    p_man.add_argument("--caso", help="ID del caso")
    p_man.add_argument("--perito", help="Nombre del perito")
    p_man.add_argument("-o", "--salida", help="Ruta de salida")
    p_man.add_argument("-e", "--extensiones", help="Extensiones a incluir")
    p_man.add_argument("-x", "--excluir", help="Patrones a excluir")
    p_man.add_argument("-v", "--verificar", action="store_true",
                       help="Verificar manifest despues de generar")
    p_man.set_defaults(func=linux_main.cmd_manifest)

    # verificar-manifest
    p_vm = sub.add_parser("verificar-manifest", help="Verificar manifest JSON")
    p_vm.add_argument("manifest", help="Ruta del manifest.json")
    p_vm.set_defaults(func=linux_main.cmd_verificar_manifest)

    # carve
    p_carve = sub.add_parser("carve", help="Recuperar archivos eliminados")
    p_carve.add_argument("fuente", nargs="?", help="Dispositivo o imagen")
    p_carve.add_argument("-o", "--salida", help="Directorio de salida")
    p_carve.add_argument("--caso", help="ID del caso")
    p_carve.add_argument("--perito", help="Nombre del perito")
    p_carve.add_argument("-c", "--config", help="Archivo de configuracion scalpel")
    p_carve.add_argument("-p", "--perfil",
                         choices=["recuperacion", "medios", "documentos", "redes", "cripto", "mensajeria", "general"],
                         help="Perfil de configuracion")
    p_carve.add_argument("--perfiles", action="store_true",
                         help="Listar perfiles disponibles")
    p_carve.add_argument("-m", "--manifest", action="store_true",
                         help="Generar manifest de carving")
    p_carve.add_argument("-v", "--verbose", action="store_true")
    p_carve.add_argument("--verificar-instalacion", action="store_true")
    p_carve.add_argument("--listar-tipos", action="store_true")
    p_carve.set_defaults(func=linux_main.cmd_carve)

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analizar resultados de scalpel")
    p_analyze.add_argument("directorio", help="Directorio de salida de scalpel")
    p_analyze.set_defaults(func=linux_main.cmd_analyze)

    # memoria
    p_mem = sub.add_parser("memoria", help="Analisis de memoria con Volatility3")
    p_mem.add_argument("--verificar-entorno", action="store_true",
                       help="Verificar herramientas disponibles")
    p_mem.add_argument("--adquirir", action="store_true",
                       help="Adquirir dump de memoria")
    p_mem.add_argument("--analizar", action="store_true",
                       help="Analizar dump con Volatility3")
    p_mem.add_argument("--verificar", action="store_true",
                       help="Verificar integridad del dump")
    p_mem.add_argument("--dump", help="Ruta del dump .raw")
    p_mem.add_argument("--plugin", default="windows.pslist",
                       help="Plugin de Volatility3")
    p_mem.add_argument("--estado", action="store_true")
    p_mem.add_argument("--cadena", action="store_true")
    p_mem.add_argument("--cifrar", help="Cifrar archivo")
    p_mem.add_argument("--firmar", help="Firmar cadena")
    p_mem.add_argument("--informe", action="store_true")
    p_mem.set_defaults(func=cmd_memoria)

    # perito
    p_perito = sub.add_parser("perito", help="Configuracion del perito")
    p_perito.add_argument("--configurar", action="store_true")
    p_perito.add_argument("--ver", action="store_true")
    p_perito.add_argument("--info", action="store_true")
    p_perito.set_defaults(func=linux_main.cmd_perito)

    # interact
    p_interact = sub.add_parser("interact", help="Modo interactivo")
    p_interact.add_argument("--caso", help="ID del caso")
    p_interact.add_argument("--perito", help="Nombre del perito")
    p_interact.add_argument("--directorio", help="Directorio de trabajo")
    p_interact.set_defaults(func=linux_main.cmd_interact)

    # bloquear
    p_bloq = sub.add_parser("bloquear",
                            help="Activar proteccion USB global contra escritura (politica de registro)")
    p_bloq.add_argument("dispositivo", nargs="?", default="",
                        help="No se usa en Windows; politica global")
    p_bloq.set_defaults(func=cmd_bloquear)

    # desbloquear
    p_desb = sub.add_parser("desbloquear",
                            help="Desactivar proteccion USB global contra escritura")
    p_desb.add_argument("dispositivo", nargs="?", default="",
                        help="No se usa en Windows; politica global")
    p_desb.set_defaults(func=cmd_desbloquear)

    # listar
    p_list = sub.add_parser("listar", help="Listar dispositivos de almacenamiento")
    p_list.add_argument("-s", "--incluir-sistema", action="store_true")
    p_list.set_defaults(func=cmd_listar)

    # daemon
    p_daemon = sub.add_parser("daemon", help="Daemon de bloqueo automatico")
    p_daemon.add_argument("accion", nargs="?", default="status",
                          choices=["status", "install", "uninstall"])
    p_daemon.set_defaults(func=_cmd_no_disponible_windows("daemon"))


def main():
    parser = argparse.ArgumentParser(
        prog="forensic_suite",
        description="ForensicSuite - Framework de Analisis Forense Digital (Windows)"
    )
    parser.add_argument("--version", action="version", version="ForensicSuite Windows 2.0.0")

    sub = parser.add_subparsers(dest="comando", help="Comandos disponibles")
    _configurar_parsers(sub)

    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
