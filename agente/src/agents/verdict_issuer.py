from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.state import EstadoEvaluacion

class VerdictIssuerAgent:
    """
    Orquestador (Cierre): Analiza las conclusiones del especialista y dicta la sentencia estructurada.
    """
    def __init__(self, config: dict):
        llm_config = config.get("llm", {})
        self.llm = ChatGroq(
            model=llm_config.get("model", "llama-3.3-70b-versatile"),
            temperature=llm_config.get("temperature", 0.1),
        )

    def __call__(self, state: EstadoEvaluacion) -> dict:
        print("[EMISOR DE VEREDICTO] Analizando informe técnico para emitir dictamen de cierre...")

        system_prompt = """
        Sos el juez de control y director administrativo de la Lotería de Santa Fe. Tu rol es revisar el informe del inspector técnico y emitir una resolución definitiva.
        Tu respuesta debe seguir OBLIGATORIAMENTE este formato estructurado:

        VEREDICTO: [Colocá únicamente una de estas opciones: APROBAR, RECHAZAR o REVISAR]
        JUSTIFICACIÓN: [Escribí una síntesis clara de máximo 3 oraciones, fundamentando la decisión en base al Anexo I]
        """

        user_prompt = f"Informe del inspector técnico:\n{state.get('reporte_especialista', '')}"

        resp = self.llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        dictamen_final = resp.content

        veredicto_limpio = "RECHAZAR" if "RECHAZAR" in dictamen_final else "APROBAR" if "APROBAR" in dictamen_final else "REVISAR"

        print("✓ [EMISOR DE VEREDICTO] Dictamen final firmado y cargado al Estado.")
        return {"veredicto_final": veredicto_limpio, "justificacion_final": dictamen_final}
