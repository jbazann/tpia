import sqlite3
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

class RuleEngine:
    """
    Herramienta RuleEngine:
    Mantiene una base de datos de reglas predefinidas.
    Evalúa reglas de forma determinista sin acceso directo al PDF.
    Gestiona sesiones del agente con estado persistente en disco.
    """
    
    def __init__(self, config=None):
        self.config = config or {}
        self.db_path = "data/rules.db"
        self.sessions_dir = "data/sessions"
        
        # Crear directorios necesarios
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
        
        # Inicializar la base de datos de reglas
        self._init_database()

    def _init_database(self):
        """Inicializa la base de datos SQLite si no existe."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de reglas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL UNIQUE,
                priority INTEGER DEFAULT 0,
                target_agent TEXT NOT NULL,
                action_type TEXT DEFAULT 'invoke_subagent',
                payload TEXT,
                is_active INTEGER DEFAULT 1
            )
        """)
        
        # Tabla de sesiones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                document_name TEXT,
                final_verdict TEXT,
                created_at TEXT,
                closed_at TEXT
            )
        """)
        
        # Tabla de evaluaciones de reglas individuales
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rule_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                rule_id INTEGER,
                rule_name TEXT,
                verdict TEXT,
                justification TEXT,
                evaluated_at TEXT,
                FOREIGN KEY(session_id) REFERENCES sessions(session_id),
                FOREIGN KEY(rule_id) REFERENCES rules(id)
            )
        """)
        
        # Insertar reglas por defecto si está vacía
        cursor.execute("SELECT COUNT(*) FROM rules")
        if cursor.fetchone()[0] == 0:
            default_rules = [
                ("run_legal_evaluation", 1, "legal_evaluation_flow", "invoke_subagent", "Analizar publicidad"),
                ("summarize_content", 2, "summarizer_agent", "invoke_subagent", "Resumir el contenido del documento"),
                ("extract_data", 3, "data_extractor_agent", "invoke_subagent", "Extraer entidades y datos estructurados"),
                ("validate_content", 4, "validator_agent", "invoke_subagent", "Validar coherencia y completitud"),
                ("finalize_analysis", 999, "final_agent", "stop", "Análisis completado")
            ]
            
            for rule_name, priority, target_agent, action_type, payload in default_rules:
                cursor.execute("""
                    INSERT INTO rules (rule_name, priority, target_agent, action_type, payload, is_active)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (rule_name, priority, target_agent, action_type, payload))
        
        conn.commit()
        conn.close()
        print("[RuleEngine] Base de datos de reglas inicializada.")

    def start_session(self, session_id: str = None, document_name: str = "Desconocido") -> str:
        """
        Inicia una nueva sesión del agente.
        Resetea el estado de las reglas evaluadas.
        Retorna el ID de sesión.
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        # Estado inicial de la sesión
        created_at = datetime.now().isoformat()
        session_state = {
            "session_id": session_id,
            "document_name": document_name,
            "created_at": created_at,
            "executed_rules": [],  # Lista de reglas ya ejecutadas
            "current_step": 0,  # Índice de la próxima regla a ejecutar
            "is_active": True
        }
        
        with open(session_file, 'w') as f:
            json.dump(session_state, f, indent=2)
            
        # Registrar en la base de datos
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO sessions (session_id, document_name, created_at)
            VALUES (?, ?, ?)
        """, (session_id, document_name, created_at))
        conn.commit()
        conn.close()
        
        print(f"[RuleEngine] Sesión iniciada: {session_id} para documento: {document_name}")
        return session_id

    def _load_session(self, session_id: str) -> dict:
        """Carga el estado de una sesión desde disco."""
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        
        if not os.path.exists(session_file):
            raise ValueError(f"Sesión no encontrada: {session_id}")
        
        with open(session_file, 'r') as f:
            return json.load(f)

    def _save_session(self, session_id: str, session_state: dict):
        """Guarda el estado de una sesión en disco."""
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        with open(session_file, 'w') as f:
            json.dump(session_state, f, indent=2)

    def get_next_rules(self, session_id: str) -> list:
        """
        Obtiene las próximas reglas a evaluar para una sesión específica.
        No requiere acceso al PDF; solo mantiene estado determinista.
        """
        session_state = self._load_session(session_id)
        
        if not session_state.get("is_active"):
            print(f"[RuleEngine] Sesión {session_id} ya fue cerrada.")
            return []
        
        # Obtener todas las reglas activas de la BD, ordenadas por prioridad
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, rule_name, target_agent, action_type, payload, priority
            FROM rules
            WHERE is_active = 1
            ORDER BY priority ASC
        """)
        all_rules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Filtrar solo reglas no ejecutadas aún
        executed_rule_ids = session_state.get("executed_rules", [])
        pending_rules = [r for r in all_rules if r["id"] not in executed_rule_ids]
        
        if not pending_rules:
            print(f"[RuleEngine] No hay más reglas pendientes para sesión {session_id}.")
            return []
        
        # Devolver la próxima regla (índice según current_step)
        next_rule = pending_rules[0]
        
        return [
            {
                "rule_id": next_rule["id"],
                "rule_name": next_rule["rule_name"],
                "action": next_rule["action_type"],
                "target_agent": next_rule["target_agent"],
                "payload": next_rule["payload"]
            }
        ]

    def submit_rule_verdict(self, session_id: str, rule_id: int, rule_name: str, verdict: str, justification: str):
        """Registra el veredicto para una regla individual en la base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO rule_evaluations (session_id, rule_id, rule_name, verdict, justification, evaluated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session_id, rule_id, rule_name, verdict, justification, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        print(f"[RuleEngine] Veredicto '{verdict}' registrado para la regla {rule_name} (ID: {rule_id}).")
        
        # Marcar regla como ejecutada para avanzar el estado
        self.mark_rule_executed(session_id, rule_id)

    def compute_final_verdict(self, session_id: str) -> str:
        """Calcula el veredicto final basado en la jerarquía de los veredictos individuales."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT verdict FROM rule_evaluations WHERE session_id = ?", (session_id,))
        evaluations = cursor.fetchall()
        
        final_verdict = "APROBAR"
        if evaluations:
            verdicts = [e[0] for e in evaluations]
            if "RECHAZAR" in verdicts:
                final_verdict = "RECHAZAR"
            elif "REVISAR" in verdicts:
                final_verdict = "REVISAR"
                
        # Actualizar la sesión en la base de datos
        cursor.execute("UPDATE sessions SET final_verdict = ? WHERE session_id = ?", (final_verdict, session_id))
        conn.commit()
        conn.close()
        
        print(f"[RuleEngine] Veredicto final calculado: {final_verdict} para sesión {session_id}.")
        return final_verdict

    def mark_rule_executed(self, session_id: str, rule_id: int):
        """Marca una regla como ejecutada en la sesión."""
        session_state = self._load_session(session_id)
        
        if rule_id not in session_state.get("executed_rules", []):
            session_state["executed_rules"].append(rule_id)
            session_state["current_step"] += 1
            self._save_session(session_id, session_state)
            print(f"[RuleEngine] Regla {rule_id} marcada como ejecutada en sesión {session_id}.")

    def close_session(self, session_id: str):
        """
        Cierra una sesión del agente.
        El estado persiste en disco para auditoría.
        """
        session_state = self._load_session(session_id)
        session_state["is_active"] = False
        session_state["closed_at"] = datetime.now().isoformat()
        self._save_session(session_id, session_state)
        print(f"[RuleEngine] Sesión cerrada: {session_id}. Estado guardado.")

    def add_custom_rule(self, rule_name: str, priority: int, target_agent: str, 
                       action_type: str = "invoke_subagent", payload: str = "") -> int:
        """Permite agregar reglas personalizadas a la base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO rules (rule_name, priority, target_agent, action_type, payload, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (rule_name, priority, target_agent, action_type, payload))
            conn.commit()
            rule_id = cursor.lastrowid
            print(f"[RuleEngine] Regla personalizada añadida: {rule_name} (ID: {rule_id})")
            return rule_id
        except sqlite3.IntegrityError:
            print(f"[RuleEngine] Error: La regla '{rule_name}' ya existe.")
            return None
        finally:
            conn.close()

    def list_rules(self) -> list:
        """Lista todas las reglas disponibles en la base de datos."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rules ORDER BY priority ASC")
        rules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rules
