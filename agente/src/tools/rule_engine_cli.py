"""
Utilidad CLI para gestionar la base de datos de reglas de RuleEngine.
Permite ver, agregar y modificar reglas sin necesidad de tocar el código.
"""
import argparse
import sys
from src.tools.rule_engine import RuleEngine
from tabulate import tabulate

def main():
    parser = argparse.ArgumentParser(description="Gestor de Reglas para RuleEngine.")
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")
    
    # Comando: list (listar todas las reglas)
    list_cmd = subparsers.add_parser("list", help="Listar todas las reglas disponibles")
    
    # Comando: add (agregar una nueva regla)
    add_cmd = subparsers.add_parser("add", help="Agregar una nueva regla a la base de datos")
    add_cmd.add_argument("-n", "--name", required=True, help="Nombre único de la regla")
    add_cmd.add_argument("-p", "--priority", type=int, required=True, help="Prioridad (número menor = ejecuta primero)")
    add_cmd.add_argument("-a", "--agent", required=True, help="Nombre del agente a invocar")
    add_cmd.add_argument("-t", "--type", default="invoke_subagent", help="Tipo de acción (invoke_subagent, stop, etc)")
    add_cmd.add_argument("--payload", default="", help="Descripción o payload de la regla")
    
    # Comando: list-sessions (listar sesiones)
    sessions_cmd = subparsers.add_parser("list-sessions", help="Listar todas las sesiones activas")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
    
    # Inicializar RuleEngine
    engine = RuleEngine()
    
    if args.command == "list":
        rules = engine.list_rules()
        if not rules:
            print("No hay reglas definidas.")
        else:
            headers = ["ID", "Nombre", "Prioridad", "Agente", "Tipo Acción", "Payload", "Activa"]
            rows = [
                [r["id"], r["rule_name"], r["priority"], r["target_agent"], 
                 r["action_type"], r["payload"][:30] + "..." if len(r["payload"]) > 30 else r["payload"],
                 "Sí" if r["is_active"] else "No"]
                for r in rules
            ]
            print("\n" + tabulate(rows, headers=headers, tablefmt="grid"))
    
    elif args.command == "add":
        rule_id = engine.add_custom_rule(
            rule_name=args.name,
            priority=args.priority,
            target_agent=args.agent,
            action_type=args.type,
            payload=args.payload
        )
        if rule_id:
            print(f"✓ Regla agregada exitosamente con ID: {rule_id}")
        else:
            sys.exit(1)
    
    elif args.command == "list-sessions":
        import os
        import json
        sessions_dir = "data/sessions"
        if not os.path.exists(sessions_dir):
            print("No hay sesiones registradas aún.")
        else:
            sessions = [f for f in os.listdir(sessions_dir) if f.endswith(".json")]
            if not sessions:
                print("No hay sesiones registradas aún.")
            else:
                print(f"\nTotal de sesiones: {len(sessions)}\n")
                for session_file in sorted(sessions):
                    session_path = os.path.join(sessions_dir, session_file)
                    with open(session_path, 'r') as f:
                        session_data = json.load(f)
                    session_id = session_data.get("session_id")
                    created_at = session_data.get("created_at")
                    is_active = session_data.get("is_active")
                    executed = len(session_data.get("executed_rules", []))
                    print(f"  • {session_id}")
                    print(f"    Creada: {created_at}")
                    print(f"    Estado: {'Activa' if is_active else 'Cerrada'}")
                    print(f"    Reglas ejecutadas: {executed}\n")

if __name__ == "__main__":
    main()
