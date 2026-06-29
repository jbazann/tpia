from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.state import EstadoEvaluacion
import os

class LegalSpecialistAgent:
    """
    Sub-agente legal: contrasta el contenido textual Y el análisis visual
    del material publicitario contra la normativa recuperada por el RAG.
    """

    def __init__(self, config: dict):
        llm_config = config.get("llm", {})
        api_key_env = llm_config.get("api_key_env_var", "GROQ_API_KEY")
        self.llm = ChatGroq(
            api_key=os.environ.get(api_key_env, ""),
            model=llm_config["model"],
            temperature=llm_config.get("temperature", 0.1),
        )

    def __call__(self, state: EstadoEvaluacion) -> dict:
        print("[ESPECIALISTA LEGAL] Evaluando compatibilidad normativa...")

        analisis_visual = state.get("analisis_visual", "").strip()
        tiene_analisis_visual = bool(analisis_visual and "no disponible" not in analisis_visual.lower())

        system_prompt = """\
Sos un inspector técnico y auditor legal de la Lotería de Santa Fe.
Tu rol es contrastar el contenido de la publicidad (texto e imágenes) contra el marco regulatorio provisto.
Analizá si la pieza publicitaria cumple o infringe la normativa.

REGLA DE ORO: Sé riguroso y formal. No inventes regulaciones. Basate ESTRICTAMENTE en las cláusulas provistas."""

        # Construir el prompt de usuario con o sin análisis visual
        seccion_visual = ""
        if tiene_analisis_visual:
            seccion_visual = f"""
Análisis visual de imágenes embebidas en el PDF (OCR + modelo de visión):
{analisis_visual}
"""

        regla_nombre = state.get("regla_nombre", "").strip()
        regla_requisito = state.get("regla_requisito", "").strip()

        seccion_regla = ""
        if regla_nombre and regla_requisito:
            seccion_regla = f"""
Regla específica a auditar:
- Canal/Nombre de Control: {regla_nombre}
- Requisitos a verificar: {regla_requisito}
"""

        user_prompt = f"""
Normativa aplicable general (recuperada del RAG):
{state.get('articulos_legales', '')}
{seccion_regla}
Contenido textual del material promocional:
{state.get('archivo_contenido', '')}
{seccion_visual}
Redactá un informe técnico detallando las concordancias detectadas o listando taxativamente cada infracción normativa encontrada con respecto a la normativa y a la regla específica provista.
Considerá tanto el texto como las imágenes en tu análisis."""

        print("\n" + "="*50)
        print("[LLM_CALL] ChatGroq - Especialista Legal")
        print(f"Model: {self.llm.model_name}")
        print("System Prompt:\n" + system_prompt)
        print("User Prompt:\n" + user_prompt)
        print("="*50 + "\n")

        resp = self.llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])

        print("\n" + "="*50)
        print("[LLM_RESPONSE] ChatGroq - Especialista Legal")
        print("Content:\n" + resp.content)
        print("="*50 + "\n")

        print("[ESPECIALISTA LEGAL] Informe normativo consolidado.")
        return {"reporte_especialista": resp.content}
