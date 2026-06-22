import re
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from src.agents.state import EstadoEvaluacion

# Regex que extrae el veredicto solo cuando aparece como valor de la clave "VEREDICTO:"
_VEREDICTO_RE = re.compile(
    r'VEREDICTO\s*:\s*(APROBAR|RECHAZAR|REVISAR)',
    re.IGNORECASE
)


def _parse_veredicto(text: str) -> str:
    """
    Extrae el veredicto desde texto estructurado del LLM.
    Busca el patrón 'VEREDICTO: <valor>' para evitar falsos positivos
    cuando la palabra aparece en contexto negativo (ej: 'no se debe RECHAZAR').
    """
    match = _VEREDICTO_RE.search(text)
    if match:
        return match.group(1).upper()
    # Fallback: si el LLM no respetó el formato, buscar en todo el texto como último recurso
    for keyword in ("RECHAZAR", "APROBAR", "REVISAR"):
        if keyword in text.upper():
            return keyword
    return "REVISAR"


class VerdictIssuerAgent:
    """
    Agente de cierre: analiza el informe del especialista legal y emite
    el dictamen final en formato estructurado.
    """
    def __init__(self, config: dict):
        llm_config = config.get("llm", {})
        self.llm = ChatGroq(
            model=llm_config.get("model", "llama-3.3-70b-versatile"),
            temperature=llm_config.get("temperature", 0.1),
        )

    def __call__(self, state: EstadoEvaluacion) -> dict:
        print("[EMISOR DE VEREDICTO] Analizando informe técnico para emitir dictamen de cierre...")

        system_prompt = """\
Sos el director de control normativo de la Lotería de Santa Fe. Revisás el informe del inspector legal y emitís la resolución definitiva.

Tu respuesta DEBE seguir EXACTAMENTE este formato:

VEREDICTO: [APROBAR | RECHAZAR | REVISAR]
JUSTIFICACIÓN: [Síntesis de máximo 3 oraciones fundamentando la decisión en el marco normativo del Anexo I]

No agregues ningún texto adicional antes o después de este esquema."""

        user_prompt = f"Informe del inspector técnico:\n{state.get('reporte_especialista', '')}"

        resp = self.llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        dictamen_final = resp.content

        veredicto_limpio = _parse_veredicto(dictamen_final)

        print(f"[EMISOR DE VEREDICTO] Dictamen emitido: {veredicto_limpio}")
        return {
            "veredicto_final": veredicto_limpio,
            "justificacion_final": dictamen_final
        }
