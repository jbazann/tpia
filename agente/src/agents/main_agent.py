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
        workflow.add_node("main_agent", self._main_agent_node)
        workflow.add_node("rag_agent", RAGAgent(config))
        workflow.add_node("legal_specialist", LegalSpecialistAgent(config))
        workflow.add_node("verdict_issuer", VerdictIssuerAgent(config))
        
        # Conectamos las aristas para formar el flujo (Hub and Spoke)
        workflow.add_edge(START, "main_agent")
        
        workflow.add_conditional_edges(
            "main_agent",
            self._route_next_agent,
            {
                "rag_agent": "rag_agent",
                "legal_specialist": "legal_specialist",
                "verdict_issuer": "verdict_issuer",
                "__end__": END
            }
        )
        
        # Luego de cada sub-agente, devolvemos el control al main_agent
        workflow.add_edge("rag_agent", "main_agent")
        workflow.add_edge("legal_specialist", "main_agent")
        workflow.add_edge("verdict_issuer", "main_agent")
        
        # Compilamos el sistema multi-agente
        self.app = workflow.compile()
        print("[SISTEMA] Flujo Multi-Agente en LangGraph compilado correctamente.")

    def _main_agent_node(self, state: EstadoEvaluacion) -> dict:
        """Nodo orquestador principal. Iterará reglas y registrará resultados."""
        print("  [MainAgent Node] Evaluando estado actual...")
        
        # Si hay un veredicto para la regla actual, guardarlo en RuleEngine
        if state.get("regla_actual") and state.get("veredicto_final"):
            regla = state["regla_actual"]
            self.rule_engine.submit_rule_verdict(
                self.session_id, 
                regla.get("rule_id"), 
                regla.get("rule_name"), 
                state.get("veredicto_final"), 
                state.get("justificacion_final", "")
            )
            
            # Limpiamos el estado para la próxima iteración
            state["regla_actual"] = None
            state["articulos_legales"] = ""
            state["reporte_especialista"] = ""
            state["veredicto_final"] = ""
            state["justificacion_final"] = ""
        
        # Si no hay regla actual o recién se limpió, pedir la próxima
        if not state.get("regla_actual"):
            next_rules = self.rule_engine.get_next_rules(self.session_id)
            if next_rules:
                regla = next_rules[0]
                if regla.get("action") == "stop":
                    print("  [*] Regla de parada detectada.")
                    self.rule_engine.mark_rule_executed(self.session_id, regla.get("rule_id"))
                    self.rule_engine.compute_final_verdict(self.session_id)
                    return state
                
                print(f"  [MainAgent Node] Iniciando evaluación para regla: {regla.get('rule_name')}")
                state["regla_actual"] = regla
            else:
                print("  [MainAgent Node] No hay más reglas. Computando veredicto final de la sesión...")
                final_verdict = self.rule_engine.compute_final_verdict(self.session_id)
                print(f"  [MainAgent Node] Veredicto Final del Documento: {final_verdict}")
                
        return state

    def _route_next_agent(self, state: EstadoEvaluacion) -> str:
        """Lógica para decidir el próximo sub-agente a invocar."""
        if not state.get("regla_actual"):
            print("  [Router] Sin reglas pendientes. Finalizando flujo.")
            return "__end__"
            
        if not state.get("articulos_legales"):
            print("  [Router] Delegando a RAGAgent...")
            return "rag_agent"
        elif not state.get("reporte_especialista"):
            print("  [Router] Delegando a LegalSpecialistAgent...")
            return "legal_specialist"
        elif not state.get("veredicto_final"):
            print("  [Router] Delegando a VerdictIssuerAgent...")
            return "verdict_issuer"
        else:
            return "main_agent"

    def run(self, pdf_context: str, prompt: str = "", document_name: str = "Documento"):
        print("=== Iniciando Agente Principal ===")
        
        # Iniciar una sesión con RuleEngine
        self.session_id = self.rule_engine.start_session(document_name=document_name)
        
        if prompt:
            print(f"Instrucción inicial recibida: '{prompt}'")
        print(f"Contexto cargado ({len(pdf_context)} caracteres).")
        
        # El Agente Principal mantiene el PDF y el prompt localmente
        self.pdf_context = pdf_context
        self.user_prompt = prompt
        
        estado_inicial = {
            "solicitud_id": f"SOL-{str(uuid.uuid4())[:8]}",
            "tipo_medio": self.user_prompt if self.user_prompt else "desconocido",
            "archivo_contenido": self.pdf_context,
            "regla_actual": None
        }
        
        try:
            print("  [LangGraph] Iniciando flujo iterativo...")
            resultado = self.app.invoke(estado_inicial)
            print("\n" + "="*50)
            print("=== FLUJO DE EVALUACIÓN COMPLETADO ===")
            print("="*50 + "\n")
        except Exception as e:
            print(f"Error durante la ejecución del grafo: {e}")
        finally:
            # Siempre cerrar la sesión, incluso si hay error
            self.rule_engine.close_session(self.session_id)
            print("\n=== Procesamiento del Agente Principal Finalizado ===")
