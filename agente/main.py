import os
import sys
import json
import argparse
import time
from pathlib import Path

# Cargar variables de entorno desde .env ANTES de cualquier otro import
# para que GROQ_API_KEY y otras variables estén disponibles
try:
    from dotenv import load_dotenv
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent

    potential_env_files = [
        base_dir / ".env",
        base_dir.parent / ".env",
        Path(".env"),
        Path("agente/.env")
    ]
    
    loaded = False
    for env_path in potential_env_files:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            print(f"[ENV] Cargado archivo de entorno desde: {env_path.resolve()}")
            loaded = True
            break
            
    if not loaded:
        print("[ENV] Advertencia: No se encontró ningún archivo .env en las rutas buscadas.")
except ImportError:
    pass  # python-dotenv no instalado; se asume que las vars de entorno ya están seteadas

# Configurar sys.path para que los imports de 'src' funcionen correctamente
if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, str(Path(__file__).parent))

# Importar los módulos principales a nivel de módulo para que PyInstaller los analice y empaquete
from src.utils.pdf_reader import read_pdf, detect_media_type
from src.agents.main_agent import MainAgent

# Manejo de rutas cuando se ejecuta desde un bundle de PyInstaller
def get_base_path():
    """Obtener la ruta base de la aplicación (funciona en desarrollo y en bundle de PyInstaller)."""
    if getattr(sys, 'frozen', False):
        # Ejecutable generado por PyInstaller
        return sys._MEIPASS
    else:
        # Modo desarrollo: usar el directorio del archivo
        return Path(__file__).parent

def load_config_from_path(config_path):
    """Cargar la configuración desde la ruta indicada."""
    import yaml
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

class TeeLogger:
    def __init__(self, filename, stream):
        self.terminal = stream
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        # Use append or write? We want the latest execution + historical is fine, but write is cleaner per execution.
        # Let's use 'w' to only keep the latest execution log to keep it simple, or 'a' to append. We use 'w'.
        self.log = open(filename, "w", encoding="utf-8")

    def write(self, message):
        try:
            self.terminal.write(message)
        except Exception:
            try:
                encoding = getattr(self.terminal, 'encoding', 'ascii') or 'ascii'
                encoded_message = message.encode(encoding, errors='replace').decode(encoding)
                self.terminal.write(encoded_message)
            except Exception:
                pass
        try:
            self.log.write(message)
            self.log.flush()
        except Exception:
            pass

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def main():
    # Inicializar Observabilidad
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent

    log_file = os.path.join(base_dir, "data", "logs", "agent_observability.log")
    sys.stdout = TeeLogger(log_file, sys.stdout)
    sys.stderr = TeeLogger(log_file, sys.stderr)

    # Configurar el parseo de argumentos por CLI
    parser = argparse.ArgumentParser(description="Sistema Multiagente para Análisis de PDFs.")
    parser.add_argument("-f", "--file", dest="pdf_path", required=True, help="Ruta al archivo PDF a procesar.")
    parser.add_argument("-p", "--prompt", dest="prompt", default="", help="Prompt o instrucción adicional para el agente.")
    # Imprimir saludo y listar argumentos recibidos al iniciarse
    print("Agente TP IA.")
    # Mostrar solo los argumentos pasados (sin el nombre del script)
    print("Argumentos recibidos:", sys.argv[1:])
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # argparse imprimirá el uso; esperar antes de terminar la ejecución
        time.sleep(5)
        raise

    try:
        # Determinar la ruta base (funciona en desarrollo y con PyInstaller)
        base_path = get_base_path()
        
        # Ajustar sys.path para que los imports funcionen dentro del bundle de PyInstaller
        if getattr(sys, 'frozen', False):
            sys.path.insert(0, base_path)
        
        # Cargar configuración: verificar múltiples ubicaciones
        config_path = None
        for potential_path in [
            os.path.join(base_path, "config.yaml"),
            os.path.join(base_path, "..", "config.yaml"),
            "config.yaml",
            os.path.join(os.path.dirname(base_path), "config.yaml"),
        ]:
            if os.path.exists(potential_path):
                config_path = potential_path
                break
        
        if not config_path:
            error_msg = "Error: config.yaml no encontrado en ninguna ubicación esperada"
            print(error_msg, file=sys.stderr)
            # Esperar antes de salir
            time.sleep(5)
            sys.exit(1)
        
        config = load_config_from_path(config_path)
        
        # 2. Validar que el archivo exista antes de procesar
        if not os.path.exists(args.pdf_path):
            error_msg = f"Error: El archivo '{args.pdf_path}' no existe."
            print(error_msg, file=sys.stderr)
            # Esperar antes de salir
            time.sleep(5)
            sys.exit(1)
        
        print(f"Procesando archivo: {args.pdf_path}")
        pdf_abs_path = os.path.abspath(args.pdf_path)
        pdf_context = read_pdf(pdf_abs_path)

        # Detectar tipo de medio automáticamente del contenido del PDF
        tipo_medio = detect_media_type(pdf_context)
        print(f"Tipo de medio detectado automáticamente: '{tipo_medio}'")

        # 3. Inicializar el agente principal e inyectar el contexto
        agent = MainAgent(config)
        agent.run(pdf_context, args.prompt, tipo_medio=tipo_medio, pdf_path=pdf_abs_path)

        
        # Exitoso
        print("\n[SUCCESS] Archivo procesado exitosamente.")
        # Esperar 5 segundos antes de terminar la ejecución
        time.sleep(5)
        sys.exit(0)
        
    except FileNotFoundError as e:
        error_msg = f"Error: Archivo no encontrado - {str(e)}"
        print(error_msg, file=sys.stderr)
        time.sleep(5)
        sys.exit(1)
    except ValueError as e:
        error_msg = f"Error: Valor inválido - {str(e)}"
        print(error_msg, file=sys.stderr)
        time.sleep(5)
        sys.exit(1)
    except ImportError as e:
        error_msg = f"Error: Módulo no encontrado - {str(e)}"
        print(error_msg, file=sys.stderr)
        time.sleep(5)
        sys.exit(1)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(error_msg, file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        time.sleep(5)
        sys.exit(1)

if __name__ == "__main__":
    main()
