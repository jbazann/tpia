import os
import sys
import json
import argparse
import time
from pathlib import Path

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

def main():
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
        
        # Importar los módulos necesarios
        from src.utils.pdf_reader import read_pdf
        from src.agents.main_agent import MainAgent
        
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
        pdf_context = read_pdf(args.pdf_path)
        
        # 3. Inicializar el agente principal e inyectar el contexto y el prompt dinámico
        agent = MainAgent(config)
        agent.run(pdf_context, args.prompt)
        
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
