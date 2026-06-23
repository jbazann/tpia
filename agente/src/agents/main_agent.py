import time
import uuid
from src.tools.rule_engine import RuleEngine
from langgraph.graph import StateGraph, START, END
from src.agents.state import EstadoEvaluacion
from src.agents.image_agent import ImageAgent
from src.agents.rag_agent import RAGAgent
from src.agents.legal_specialist import LegalSpecialistAgent
from src.agents.verdict_issuer import VerdictIssuerAgent


class MainAgent:
    """
    Agente principal que coordina el sistema multi-agente.

    Flujo LangGraph:
        image_agent  →  rag_agent  →  legal_specialist  →  verdict_issuer

    El ImageAgent analiza imágenes embebidas (OCR + visión LLM).
    El RAGAgent recupera normativa relevante según el tipo de medio.
    El LegalSpecialist contrasta texto + análisis visual contra la normativa.
    El VerdictIssuer emite el dictamen final estructurado.
    """

    def __init__(self, config: dict):
        self.config = config
        self.rule_engine = RuleEngine(config)
        self.session_id = None
        self.pdf_path = None  # Se establece en run()

    def _init_langgraph(self, pdf_path: str):
        """Construye el grafo LangGraph inyectando el pdf_path al ImageAgent."""
        workflow = StateGraph(EstadoEvaluacion)

        workflow.add_node("image_agent",       ImageAgent(self.config, pdf_path))
        workflow.add_node("rag_agent",         RAGAgent(self.config))
        workflow.add_node("legal_specialist",  LegalSpecialistAgent(self.config))
        workflow.add_node("verdict_issuer",    VerdictIssuerAgent(self.config))

        # Flujo secuencial según la arquitectura propuesta
        workflow.add_edge(START,             "image_agent")
        workflow.add_edge("image_agent",     "rag_agent")
        workflow.add_edge("rag_agent",       "legal_specialist")
        workflow.add_edge("legal_specialist", "verdict_issuer")
        workflow.add_edge("verdict_issuer",  END)

        self.app = workflow.compile()
        print("[SISTEMA] Grafo multi-agente LangGraph compilado correctamente.")
        print("[SISTEMA] Flujo: ImageAgent → RAGAgent → LegalSpecialist → VerdictIssuer")

    def run(self, pdf_context: str, prompt: str = "", tipo_medio: str = "general", pdf_path: str = ""):
        """
        Ejecuta el pipeline completo de auditoría.

        Args:
            pdf_context: Texto extraído del PDF.
            prompt:      Instrucción adicional del usuario (opcional).
            tipo_medio:  Tipo de medio detectado automáticamente.
            pdf_path:    Ruta al PDF original (necesaria para el ImageAgent).
        """
        print("=== Iniciando Agente Principal ===")

        self.pdf_path = pdf_path
        self._init_langgraph(pdf_path)  # Reconstruir grafo con el pdf_path correcto
        self.session_id = self.rule_engine.start_session()

        print(f"Tipo de medio detectado : '{tipo_medio}'")
        print(f"Contexto textual        : {len(pdf_context)} caracteres")
        if prompt:
            print(f"Instrucción del usuario : '{prompt}'")

        loop_counter = 0
        max_iterations = 10
        
        final_verdict = None
        final_justification = None

        try:
            while loop_counter < max_iterations:
                print(f"\n--- Iteración {loop_counter + 1} ---")

                next_rules = self.rule_engine.get_next_rules(self.session_id)
                if not next_rules:
                    print("[*] No hay más reglas pendientes. Finalizando.")
                    break

                should_stop = False
                for rule in next_rules:
                    rule_id   = rule.get("rule_id")
                    action    = rule.get("action")
                    rule_name = rule.get("rule_name")
                    target    = rule.get("target_agent")

                    print(f"  [Rule] '{rule_name}' → {target}")

                    if action == "invoke_subagent":
                        if target == "legal_evaluation_flow":
                            print(f"  [LangGraph] Iniciando flujo multi-agente...")
                            print(f"  [LangGraph] Sub-agentes que serán invocados secuencialmente: ImageAgent -> RAGAgent -> LegalSpecialist -> VerdictIssuer")

                            estado_inicial = {
                                "solicitud_id":      f"SOL-{str(uuid.uuid4())[:8].upper()}",
                                "tipo_medio":        tipo_medio,
                                "archivo_contenido": pdf_context,
                                "analisis_visual":   "",  # El ImageAgent lo completará
                                "regla_nombre":      rule_name,
                                "regla_requisito":   rule.get("payload", ""),
                            }

                            resultado = self.app.invoke(estado_inicial)
                            
                            final_verdict = resultado.get('veredicto_final')
                            final_justification = resultado.get('justificacion_final')

                            print("\n" + "=" * 55)
                            print(f"RESULTADO DE LA EVALUACIÓN (Regla: '{rule_name}')")
                            print("=" * 55)
                            print(f"Veredicto : {final_verdict}")
                            print(f"Dictamen  :\n{final_justification}")
                            print("=" * 55 + "\n")

                        else:
                            print(f"  [INFO] Agente '{target}' no implementado. Saltando.")

                        self.rule_engine.mark_rule_executed(self.session_id, rule_id)

                    elif action == "stop":
                        print(f"  [*] Regla de parada: '{rule_name}'.")
                        self.rule_engine.mark_rule_executed(self.session_id, rule_id)
                        should_stop = True
                        break

                if should_stop:
                    break

                loop_counter += 1
                time.sleep(0.3)

        finally:
            self.rule_engine.close_session(self.session_id)
            
            print("\n" + "★" * 65)
            print("★ RESULTADO FINAL DEL PROCESAMIENTO (RESUMEN)")
            print("★" * 65)
            if final_verdict:
                print(f"★ VEREDICTO DEFINITIVO : {final_verdict}")
                print(f"★ JUSTIFICACIÓN FINAL  :\n{final_justification}")
            else:
                print("★ No se emitió ningún veredicto durante el flujo.")
            print("★" * 65 + "\n")
            
            print("=== Procesamiento finalizado ===")
