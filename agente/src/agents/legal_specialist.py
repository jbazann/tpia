from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.state import EstadoEvaluacion

class LegalSpecialistAgent:
    """
    Sub-Agente Orquestado: Procesa el lenguaje natural contrastando 
    el RAG contra el contenido de la pieza publicitaria.
    """
    def __init__(self, config: dict):
        llm_config = config.get("llm", {})
        self.llm = ChatGroq(
            model=llm_config.get("model", "llama-3.3-70b-versatile"),
            temperature=llm_config.get("temperature", 0.1),
        )

    def __call__(self, state: EstadoEvaluacion) -> dict:
        print(f"[ESPECIALISTA] Evaluando compatibilidad normativa mediante PLN cognitivo...")

        regla = state.get('regla_actual', {})
        regla_nombre = regla.get('rule_name', 'Evaluación general')
        regla_desc = regla.get('payload', '')

        system_prompt = f"""
        Sos un inspector técnico y auditor legal de la Lotería de Santa Fe. Tu único rol es contrastar el contenido de la publicidad contra el marco regulatorio provisto,
        enfocándote ESPECÍFICAMENTE en la siguiente regla o criterio: {regla_nombre} ({regla_desc}).
        Analizá detalladamente si la pieza publicitaria cumple o si infringe la norma en este aspecto específico.

        REGLA DE ORO: Sé riguroso y formal. No inventes regulaciones. Basate ESTRICTAMENTE en las cláusulas provistas en el contexto.
        """

        user_prompt = f"""
        Normativa aplicable vigente (Inyectada dinámicamente desde el RAG):
        {state.get('articulos_legales', '')}

        Contenido del material promocional a evaluar (Extraído por el procesador de archivos):
        {state.get('archivo_contenido', '')}

        Redactá un informe técnico detallando las concordancias detectadas o listando taxativamente cada una de las infracciones normativas encontradas.
        """

        resp = self.llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        
        print("✓ [ESPECIALISTA] Informe normativo consolidado en el Estado.")
        return {"reporte_especialista": resp.content}
