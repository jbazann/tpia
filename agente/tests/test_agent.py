import os
import unittest
import tempfile
import sqlite3
from pathlib import Path

# Agregar src al sys.path para imports en tests
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.pdf_reader import detect_media_type
from src.tools.rule_engine import RuleEngine


class TestPdfReader(unittest.TestCase):
    def test_detect_media_type_radial(self):
        text = "Este es un anuncio de radio con un locutor hablando en el spot radial."
        self.assertEqual(detect_media_type(text), "radial")

    def test_detect_media_type_video(self):
        text = "Placa final del spot televisivo en formato de video para la televisión."
        self.assertEqual(detect_media_type(text), "video")

    def test_detect_media_type_pnt(self):
        text = "Mención especial realizada por el periodista e influencer como PNT."
        self.assertEqual(detect_media_type(text), "pnt")

    def test_detect_media_type_grafica(self):
        text = "Aviso gráfico en el banner del cartel de vía pública."
        self.assertEqual(detect_media_type(text), "grafica")

    def test_detect_media_type_general(self):
        text = "Cualquier otro contenido publicitario institucional."
        self.assertEqual(detect_media_type(text), "general")


class TestRuleEngine(unittest.TestCase):
    def setUp(self):
        # Crear directorios temporales para no pisar la DB productiva
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "rules.db")
        self.sessions_dir = os.path.join(self.temp_dir.name, "sessions")

        # Instanciar el RuleEngine apuntando al directorio temporal
        self.engine = RuleEngine()
        self.engine.db_path = self.db_path
        self.engine.sessions_dir = self.sessions_dir
        os.makedirs(self.sessions_dir, exist_ok=True)
        self.engine._init_database()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_database_initialization(self):
        self.assertTrue(os.path.exists(self.db_path))
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rules'")
        table_exists = cursor.fetchone()
        self.assertIsNotNone(table_exists)
        
        # Debe inicializarse vacía
        cursor.execute("SELECT COUNT(*) FROM rules")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 0)
        conn.close()

    def test_session_lifecycle_with_custom_rules(self):
        # Insertar reglas manualmente para simular carga del usuario
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.executemany("""
            INSERT INTO rules (rule_name, priority, target_agent, action_type, payload, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, [
            ("Publicidad Radial", 10, "legal_evaluation_flow", "invoke_subagent", "Debe locutarse mensaje final"),
            ("Publicidad Grafica", 20, "legal_evaluation_flow", "invoke_subagent", "Leyenda de zocalo >= 10%")
        ])
        conn.commit()
        conn.close()

        # Iniciar sesión
        session_id = self.engine.start_session()
        self.assertIsNotNone(session_id)
        session_file = os.path.join(self.sessions_dir, f"{session_id}.json")
        self.assertTrue(os.path.exists(session_file))

        # Recuperar reglas pendientes (debería retornar la de menor prioridad primero: prioridad 10)
        rules = self.engine.get_next_rules(session_id)
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["rule_name"], "Publicidad Radial")

        # Marcar regla ejecutada
        self.engine.mark_rule_executed(session_id, rules[0]["rule_id"])
        
        # Recuperar siguiente regla (debería ser prioridad 20)
        next_rules = self.engine.get_next_rules(session_id)
        self.assertEqual(len(next_rules), 1)
        self.assertEqual(next_rules[0]["rule_name"], "Publicidad Grafica")

        # Cerrar sesión
        self.engine.close_session(session_id)
        state = self.engine._load_session(session_id)
        self.assertFalse(state["is_active"])


if __name__ == "__main__":
    unittest.main()
