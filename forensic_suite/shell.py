"""
ForensicSuite - Shell Interactivo (modo framework)
"""

import sys
import os
import shlex
import readline
import glob
from pathlib import Path


class ForensicShell:
    """Shell interactivo tipo Metasploit para ForensicSuite"""
    
    def __init__(self):
        self.running = True
        self.current_dir = os.getcwd()
        self.case_id = None
        self.perito_name = None
        self.evidence_dir = None
        self.history = []
        self.comandos_disponibles = {
            'hash': 'Calcular hashes criptograficos',
            'verificar': 'Verificar hash de un archivo',
            'bloquear': 'Bloquear escritura de dispositivo',
            'desbloquear': 'Desbloquear dispositivo',
            'listar': 'Listar dispositivos de almacenamiento',
            'acta': 'Generar acta de cadena de custodia',
            'firmar': 'Firmar archivo con GPG',
            'verificar-firma': 'Verificar firma GPG',
            'claves': 'Listar claves GPG',
            'timestamp': 'Obtener sello de tiempo RFC 3161',
            'verificar-timestamp': 'Verificar sello de tiempo',
            'manifest': 'Generar manifest JSON',
            'verificar-manifest': 'Verificar manifest',
            'carve': 'Recuperar archivos eliminados',
            'analyze': 'Analizar resultados de scalpel',
            'memoria': 'Adquisicion y analisis de memoria',
            'perito': 'Configuracion del perito',
            'daemon': 'Daemon de bloqueo automatico',
        }
        
        # Configurar autocompletado
        readline.set_completer(self.completer)
        readline.parse_and_bind("tab: complete")
        readline.set_completer_delims(' \t\n;')

    def completer(self, text, state):
        """Logica de autocompletado"""
        line = readline.get_line_buffer()
        args = shlex.split(line)
        
        # Comandos disponibles para completar
        lista_comandos = sorted(list(self.comandos_disponibles.keys()) + 
                                ['salir', 'ayuda', 'help', 'caso', 'perito', 'cd', 'ls', 'estado', 'clear', 'historial'])
        
        if not line or len(args) == 0:
            options = lista_comandos
        elif len(args) == 1 and not line.endswith(' '):
            options = [c for c in lista_comandos if c.startswith(text)]
        else:
            # Autocompletado de archivos/directorios
            options = [os.path.basename(p) for p in glob.glob(os.path.join(self.current_dir, text + '*'))]
            
        if state < len(options):
            return options[state]
        else:
            return None
    
    def mostrar_prompt(self):
        """Muestra el prompt del shell"""
        case_str = f"[{self.case_id}]" if self.case_id else ""
        dir_str = os.path.basename(self.current_dir) if self.current_dir else "~"
        return f"\033[1;32mforensic\033[0m{case_str} \033[1;34m{dir_str}\033[0m > "
    
    def _registrar_auditoria(self, comando):
        """Registra y firma el comando ejecutado bajo estructura de caso"""
        from datetime import datetime
        from forensic_suite.core.firma_gpg import ForensicGPG
        
        # 1. Determinar base: Caso ID o 'CASO_PENDIENTE'
        base_dir = Path(self.current_dir) / (self.case_id or "CASO_PENDIENTE")
        
        # 2. Estructura normada: CASO / AUDITORIA / <FECHA>
        log_dir = base_dir / "AUDITORIA"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 3. Nombre de archivo con marca de tiempo precisa
        fecha_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"audit_{fecha_str}.log"
        
        # 4. Formato de entrada cumpliendo registro forense
        timestamp = datetime.now().isoformat()
        perito = self.perito_name or "PERITO_NO_CONFIGURADO"
        
        entrada = f"[{timestamp}] Caso: {self.case_id or 'N/A'} | Perito: {perito} | Cmd: {comando}\n"
        
        # 5. Guardar y Firmar
        with open(log_file, "a") as f:
            f.write(entrada)
            
        gpg = ForensicGPG()
        gpg.firmar(str(log_file))
        
        # Feedback discreto
        print(f"  \033[90m[Auditoria registrada: {log_dir.parent.name}/{log_dir.name}]\033[0m")

    def ejecutar_comando(self, linea):
        """Ejecuta un comando del shell"""
        if not linea.strip():
            return
        
        self.history.append(linea)
        
        # Registrar auditoria
        self._registrar_auditoria(linea)
        
        try:
            args = shlex.split(linea)
        except ValueError as e:
            print(f"Error de sintaxis: {e}")
            return
        
        if not args:
            return
        
        cmd = args[0].lower()
        cmd_args = args[1:]
        
        # Comandos especiales del shell
        if cmd in ('salir', 'exit', 'quit'):
            self.running = False
            print("Saliendo del modo interactivo...")
            return
        
        if cmd == 'ayuda' or cmd == 'help':
            self.mostrar_ayuda(cmd_args)
            return
        
        if cmd == 'caso':
            self.configurar_caso(cmd_args)
            return
        
        if cmd == 'perito':
            self.configurar_perito(cmd_args)
            return
        
        if cmd == 'directorio' or cmd == 'cd':
            self.cambiar_directorio(cmd_args)
            return
        
        if cmd == 'pwd':
            print(self.current_dir)
            return
        
        if cmd == 'ls':
            self.listar_archivos(cmd_args)
            return
        
        if cmd == 'limpiar' or cmd == 'clear':
            os.system('clear' if os.name != 'nt' else 'cls')
            return
        
        if cmd == 'historial':
            self.mostrar_historial()
            return
        
        if cmd == 'estado':
            self.mostrar_estado()
            return
        
        # Ejecutar comando de forensic_suite
        self.ejecutar_forensic_cmd(cmd, cmd_args)
    
    def ejecutar_forensic_cmd(self, cmd, args):
        """Ejecuta un comando de forensic_suite"""
        import subprocess
        
        # Construir comando completo
        full_cmd = ['forensic_suite', cmd] + args
        
        try:
            # Ejecutar y mostrar salida en tiempo real
            proceso = subprocess.Popen(
                full_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=self.current_dir
            )
            
            for linea in proceso.stdout:
                print(linea, end='')
            
            proceso.wait()
            
            if proceso.returncode != 0:
                print(f"\nError: codigo de salida {proceso.returncode}")
                
        except FileNotFoundError:
            print("Error: forensic_suite no encontrado en PATH")
        except KeyboardInterrupt:
            print("\nCancelado por el usuario")
            proceso.kill()
        except Exception as e:
            print(f"Error: {e}")
    
    def mostrar_ayuda(self, args):
        """Muestra ayuda"""
        if args:
            # Ayuda de un comando especifico
            cmd = args[0]
            import subprocess
            try:
                subprocess.run(['forensic_suite', cmd, '--help'], cwd=self.current_dir)
            except:
                print(f"Comando no encontrado: {cmd}")
        else:
            # Ayuda general
            print("""
  ╔═══════════════════════════════════════════════════════════════╗
  ║                 AYUDA - MODO INTERACTIVO                     ║
  ╚═══════════════════════════════════════════════════════════════╝

  COMANDOS DEL SHELL:
  ───────────────────
  help [comando]     Mostrar ayuda
  caso <id>          Configurar ID del caso actual
  perito <nombre>    Configurar nombre del perito
  cd <dir>           Cambiar directorio
  pwd                Mostrar directorio actual
  ls [dir]           Listar archivos
  clear              Limpiar pantalla
  historial          Mostrar historial de comandos
  estado             Mostrar estado actual
  salir              Salir del modo interactivo

  COMANDOS FORENSICS:
  ───────────────────""")
            
            for cmd, desc in sorted(self.comandos_disponibles.items()):
                print(f"  {cmd:20s} {desc}")
            
            print("""
  EJEMPLOS:
  ─────────
  forensic> hash evidencia.raw -g
  forensic> verificar evidencia.raw.hash
  forensic> bloquear /dev/sdc
  forensic> listar
  forensic> acta evidencia.raw --perito "Juan"
  forensic> timestamp evidencia.raw
  forensic> carve evidencia.raw -p general -o recuperados/
  forensic> manifest ./evidencia/ --caso MP-001
  forensic> salir
""")
    
    def configurar_caso(self, args):
        """Configura el ID del caso actual"""
        if args:
            self.case_id = args[0]
            print(f"Caso configurado: {self.case_id}")
        else:
            if self.case_id:
                print(f"Caso actual: {self.case_id}")
            else:
                print("Uso: caso <id_del_caso>")
                print("Ejemplo: caso MP-2024-001")
    
    def configurar_perito(self, args):
        """Configura el nombre del perito"""
        if args:
            self.perito_name = ' '.join(args)
            print(f"Perito configurado: {self.perito_name}")
        else:
            if self.perito_name:
                print(f"Perito actual: {self.perito_name}")
            else:
                print("Uso: perito <nombre>")
                print("Ejemplo: perito Juan Perez")
    
    def cambiar_directorio(self, args):
        """Cambia el directorio actual"""
        if not args:
            self.current_dir = os.path.expanduser("~")
        else:
            new_dir = os.path.expanduser(args[0])
            if os.path.exists(new_dir):
                self.current_dir = os.path.abspath(new_dir)
            else:
                print(f"Directorio no encontrado: {args[0]}")
    
    def listar_archivos(self, args):
        """Lista archivos del directorio actual"""
        dir_path = args[0] if args else self.current_dir
        
        try:
            items = os.listdir(dir_path)
            for item in sorted(items):
                full_path = os.path.join(dir_path, item)
                if os.path.isdir(full_path):
                    print(f"  \033[1;34m{item}/\033[0m")
                else:
                    size = os.path.getsize(full_path)
                    print(f"  {item:30s} {size:>10,} bytes")
        except Exception as e:
            print(f"Error: {e}")
    
    def mostrar_historial(self):
        """Muestra el historial de comandos"""
        if not self.history:
            print("No hay comandos en el historial")
        else:
            for i, cmd in enumerate(self.history, 1):
                print(f"  {i:3d}  {cmd}")
    
    def mostrar_estado(self):
        """Muestra el estado actual del shell"""
        print(f"""
  ╔═══════════════════════════════════════════════════════════════╗
  ║                    ESTADO ACTUAL                             ║
  ╚═══════════════════════════════════════════════════════════════╝

  Caso:           {self.case_id or 'No configurado'}
  Perito:         {self.perito_name or 'No configurado'}
  Directorio:     {self.current_dir}
  Comandos:       {len(self.history)}
""")
    
    def ejecutar(self):
        """Ejecuta el shell interactivo"""
        from forensic_suite.banner import mostrar_banner_inicio
        
        mostrar_banner_inicio()
        
        while self.running:
            try:
                linea = input(self.mostrar_prompt())
                self.ejecutar_comando(linea)
            except KeyboardInterrupt:
                print("\n(use 'salir' paraSalir)")
            except EOFError:
                print("\nSaliendo...")
                break
            except Exception as e:
                print(f"Error: {e}")
        
        print("Modo interactivo finalizado.")
        print(f"Comandos ejecutados: {len(self.history)}")


def main():
    """Punto de entrada para modo interactivo"""
    shell = ForensicShell()
    shell.ejecutar()


if __name__ == "__main__":
    main()
