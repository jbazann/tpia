import time
import uuid
from src.tools.rule_engine import RuleEngine
from langgraph.graph import StateGraph, START, END
from src.agents.state import EstadoEvaluacion
from src.agents.rag_agent import RAGAgent
from src.agents.legal_specialist import LegalSpecialistAgent
from src.agents.verdict_issuer import VerdictIssuerAgent

class MainAgent:
    """
    El Agente Principal que coordina el sistema.
    Opera en un loop, leyendo del contexto del PDF, consultando 
    la RuleEngine (sin acceso al PDF) y ejecutando el flujo LangGraph.
    """
    def __init__(self, config: dict):
        self.config = config
        self.rule_engine = RuleEngine(config)
        self.session_id = None
        
        # Inicializar el LangGraph
        self._init_langgraph(config)

    def _init_langgraph(self, config: dict):
        workflow = StateGraph(EstadoEvaluacion)
        
        # Agregamos los nodos al grafo tipado
        workflow.add_node("rag_agent", RAGAgent(config))
        workflow.add_node("legal_specialist", LegalSpecialistAgent(config))
        workflow.add_node("verdict_issuer", VerdictIssuerAgent(config))
        
        # Conectamos las aristas para formar el flujo
        workflow.add_edge(START, "rag_agent")
        workflow.add_edge("rag_agent", "legal_specialist")
        workflow.add_edge("legal_specialist", "verdict_issuer")
        workflow.add_edge("verdict_issuer", END)
        
        # Compilamos el sistema multi-agente
        self.app = workflow.compile()
        print("[SISTEMA] Flujo Multi-Agente en LangGraph compilado correctamente.")

    def run(self, pdf_context: str, prompt: str = ""):
        print("=== Iniciando Agente Principal ===")
        
        # Iniciar una sesión con RuleEngine
        self.session_id = self.rule_engine.start_session()
        
        if prompt:
            print(f"Instrucción inicial recibida: '{prompt}'")
        print(f"Contexto cargado ({len(pdf_context)} caracteres).")
        
        # El Agente Principal mantiene el PDF y el prompt localmente
        self.pdf_context = pdf_context
        self.user_prompt = prompt
        
        loop_counter = 0
        max_iterations = 10  # Límite de seguridad
        
        try:
            while loop_counter < max_iterations:
                print(f"\n--- Iteración del Loop: {loop_counter + 1} ---")
                
                # 1. El Agente Principal consulta a RuleEngine por la próxima regla
                next_rules = self.rule_engine.get_next_rules(self.session_id)
                
                if not next_rules:
                    print("[*] No hay más reglas pendientes. Finalizando sesión.")
                    break
                
                # 2. El Agente Principal interpreta la regla
                should_stop = False
                for rule in next_rules:
                    rule_id = rule.get("rule_id")
                    action = rule.get("action")
                    rule_name = rule.get("rule_name")
                    target = rule.get("target_agent")
                    payload = rule.get("payload")
                    
                    print(f"  [Rule] Ejecutando: {rule_name} (Target: {target})")
                    
                    if action == "invoke_subagent":
                        if target == "legal_evaluation_flow":
                            print(f"  [LangGraph] Iniciando flujo de evaluación legal...")
                            estado_inicial = {
                                "solicitud_id": f"SOL-{str(uuid.uuid4())[:8]}",
                                "tipo_medio": self.user_prompt if self.user_prompt else "desconocido",
                                "archivo_contenido": self.pdf_context
                            }
                            
                            resultado = self.app.invoke(estado_inicial)
                            
                            print("\n" + "="*50)
                            print("=== RESULTADO DE LA EVALUACIÓN ===")
                            print("="*50)
                            print(f"Veredicto: {resultado.get('veredicto_final')}")
                            print(f"Justificación:\n{resultado.get('justificacion_final')}")
                            print("="*50 + "\n")
                            
                        else:
                            print(f"  [SubAgent Placeholder] Tarea: {target} - {payload}")
                            
                        # Marcar la regla como ejecutada
                        self.rule_engine.mark_rule_executed(self.session_id, rule_id)
                        
                    elif action == "stop":
                        print(f"  [*] Regla de parada detectada: {rule_name}")
                        self.rule_engine.mark_rule_executed(self.session_id, rule_id)
                        should_stop = True
                        break
                
                if should_stop:
                    break
                    
                loop_counter += 1
                time.sleep(0.5)  # Pequeña pausa entre iteraciones
                
        finally:
            # Siempre cerrar la sesión, incluso si hay error
            self.rule_engine.close_session(self.session_id)
            print("\n=== Procesamiento del Agente Principal Finalizado ===")
