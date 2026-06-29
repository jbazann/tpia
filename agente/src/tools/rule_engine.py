import sqlite3
import json
import os
import uuid
import glob
from datetime import datetime, timedelta
from pathlib import Path


class RuleEngine:
    """
    Motor de reglas determinista.
    Gestiona las reglas de ejecución del agente desde SQLite
    y el estado de sesiones desde archivos JSON con TTL de limpieza automática.
    """

    SESSION_TTL_HOURS = 24  # Sesiones más viejas que esto se eliminan automáticamente

    def __init__(self, config=None):
        self.config = config or {}

        import sys
        # Si está congelado en PyInstaller, usar la ubicación del ejecutable real
        if getattr(sys, 'frozen', False):
            base_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).parent.parent.parent

        # Buscar si la base ya existe en algún candidato compartido para coordinarse con el dashboard
        candidates = [
            base_dir / "data" / "rules.db",
            base_dir / "agente" / "data" / "rules.db",
            base_dir.parent / "agente" / "data" / "rules.db",
            Path("data/rules.db"),
            Path("agente/data/rules.db")
        ]
        
        selected_db = None
        for c in candidates:
            try:
                if c.exists():
                    selected_db = c
                    break
            except Exception:
                pass
                
        if selected_db:
            self.db_path = str(selected_db.resolve())
        else:
            self.db_path = str((base_dir / "data" / "rules.db").resolve())

        self.sessions_dir = str((base_dir / "data" / "sessions").resolve())

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)

        self._init_database()
        self._cleanup_old_sessions()  # Limpiar sesiones viejas en cada inicio

    def _init_database(self):
        """Inicializa el esquema SQLite y carga reglas por defecto si está vacía."""
        db_exists = os.path.exists(self.db_path)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if not db_exists:
            cursor.execute("""
                CREATE TABLE rules (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name   TEXT    NOT NULL UNIQUE,
                    priority    INTEGER DEFAULT 0,
                    target_agent TEXT   NOT NULL,
                    action_type TEXT    DEFAULT 'invoke_subagent',
                    payload     TEXT,
                    is_active   INTEGER DEFAULT 1
                )
            """)
            print("[RuleEngine] Base de datos de reglas creada.")

        # Verificar si hay reglas y popular si está vacía
        cursor.execute("SELECT COUNT(*) FROM rules")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO rules (rule_name, priority, target_agent, action_type, payload, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, [
                ("grafica_presencia_logo", 10, "legal_evaluation_flow", "invoke_subagent", "Validar a través del análisis visual que la pieza publicitaria contenga de forma clara y visible el logo oficial de 'Lotería de Santa Fe'. Indicar si se encuentra o si está ausente."),
                ("grafica_leyendas_obligatorias", 20, "legal_evaluation_flow", "invoke_subagent", "Verificar mediante el texto extraído y el OCR visual la presencia textual EXACTA de las dos frases obligatorias: 'SOLO PARA MAYORES DE 18 AÑOS' y 'EL JUGAR COMPULSIVAMENTE ES PERJUDICIAL PARA LA SALUD'. Reportar cualquier omisión o alteración en el texto."),
                ("grafica_formato_zocalo", 30, "legal_evaluation_flow", "invoke_subagent", "Evaluar la disposición visual de las leyendas. Éstas deben estar agrupadas junto al logo de Lotería de Santa Fe, ubicadas estrictamente AL PIE de la pieza gráfica, y deben ocupar la totalidad del espacio horizontal (100% del ancho). Además, la altura de este zócalo debe ser visualmente igual o mayor al 10% de la altura total del anuncio."),
                ("grafica_excepcion_indumentaria", 40, "legal_evaluation_flow", "invoke_subagent", "Si la pieza gráfica corresponde claramente a un espacio alternativo donde el zócalo estándar no aplica (por ejemplo, diseño de camisetas o indumentaria), validar que se cumpla la excepción del Artículo 5: debajo de la marca de la empresa debe estar en dos renglones la leyenda 'SOLO PARA MAYORES DE 18 AÑOS' junto al logo de Lotería de Santa Fe. Si es un banner gráfico tradicional, ignorar esta validación."),
                ("cierre_auditoria", 100, "none", "stop", "Fin de la evaluación del PDF.")
            ])
            print("[RuleEngine] Nuevas reglas para publicidad gráfica insertadas con éxito.")

        conn.commit()
        conn.close()

    # ──────────────────────────────────────────────
    # Sesiones
    # ──────────────────────────────────────────────

    def start_session(self, session_id: str = None) -> str:
        if session_id is None:
            session_id = str(uuid.uuid4())

        session_state = {
            "session_id":    session_id,
            "created_at":    datetime.now().isoformat(),
            "executed_rules": [],
            "current_step":  0,
            "is_active":     True,
        }

        self._save_session(session_id, session_state)
        print(f"[RuleEngine] Sesión iniciada: {session_id}")
        return session_id

    def _load_session(self, session_id: str) -> dict:
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        if not os.path.exists(session_file):
            raise ValueError(f"Sesión no encontrada: {session_id}")
        with open(session_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_session(self, session_id: str, session_state: dict):
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_state, f, indent=2, ensure_ascii=False)

    def _cleanup_old_sessions(self):
        """Elimina archivos de sesión más viejos que SESSION_TTL_HOURS."""
        cutoff = datetime.now() - timedelta(hours=self.SESSION_TTL_HOURS)
        pattern = os.path.join(self.sessions_dir, "*.json")
        removed = 0
        for filepath in glob.glob(pattern):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
                if created_at < cutoff:
                    os.remove(filepath)
                    removed += 1
            except Exception:
                pass  # Ignorar archivos corruptos o no legibles
        if removed:
            print(f"[RuleEngine] {removed} sesión(es) antigua(s) eliminada(s).")

    # ──────────────────────────────────────────────
    # Lógica de reglas
    # ──────────────────────────────────────────────

    def get_next_rules(self, session_id: str) -> list:
        print(f"[RuleEngine] Buscando próxima regla para la sesión {session_id}...")
        session_state = self._load_session(session_id)

        if not session_state.get("is_active"):
            print("[RuleEngine] La sesión no está activa.")
            return []

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

        executed_ids = session_state.get("executed_rules", [])
        pending = [r for r in all_rules if r["id"] not in executed_ids]

        if not pending:
            print("[RuleEngine] No hay reglas pendientes en la base de datos para esta sesión.")
            return []

        next_rule = pending[0]
        print(f"[RuleEngine] Regla obtenida: '{next_rule['rule_name']}' (Acción: {next_rule['action_type']}, Destino: {next_rule['target_agent']})")
        return [{
            "rule_id":      next_rule["id"],
            "rule_name":    next_rule["rule_name"],
            "action":       next_rule["action_type"],
            "target_agent": next_rule["target_agent"],
            "payload":      next_rule["payload"],
        }]

    def mark_rule_executed(self, session_id: str, rule_id: int):
        session_state = self._load_session(session_id)
        if rule_id not in session_state.get("executed_rules", []):
            session_state["executed_rules"].append(rule_id)
            session_state["current_step"] += 1
            self._save_session(session_id, session_state)
            print(f"[RuleEngine] Regla {rule_id} ejecutada.")

    def close_session(self, session_id: str):
        session_state = self._load_session(session_id)
        session_state["is_active"] = False
        session_state["closed_at"] = datetime.now().isoformat()
        self._save_session(session_id, session_state)
        print(f"[RuleEngine] Sesión cerrada: {session_id}")

    def add_custom_rule(self, rule_name: str, priority: int, target_agent: str,
                        action_type: str = "invoke_subagent", payload: str = "") -> int | None:
        """Agrega una regla personalizada a la base de datos."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO rules (rule_name, priority, target_agent, action_type, payload, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (rule_name, priority, target_agent, action_type, payload))
            conn.commit()
            rule_id = cursor.lastrowid
            print(f"[RuleEngine] Regla añadida: '{rule_name}' (ID: {rule_id})")
            return rule_id
        except sqlite3.IntegrityError:
            print(f"[RuleEngine] Error: La regla '{rule_name}' ya existe.")
            return None
        finally:
            conn.close()

    def list_rules(self) -> list:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rules ORDER BY priority ASC")
        rules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rules
