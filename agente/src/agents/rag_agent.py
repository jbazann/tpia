from src.agents.state import EstadoEvaluacion
from src.utils.rag_retriever import get_hybrid_retriever

class RAGAgent:
    """
    Sub-Agente responsable de recuperar el marco normativo 
    correspondiente según el tipo de medio a evaluar.
    """
    def __init__(self, config: dict):
        self.retriever = get_hybrid_retriever(config)

    def __call__(self, state: EstadoEvaluacion) -> dict:
        print(f"\n[ORQUESTADOR RAG] Planificando evaluación para la Solicitud {state.get('solicitud_id', 'N/A')}")
        
        tipo_medio = state.get('tipo_medio', '')
        query_busqueda = f"Publicidad {tipo_medio}"
        
        chunks_recuperados = self.retriever.invoke(query_busqueda)
        contexto_ley = "\n\n".join([f"[{c.metadata['titulo']}]: {c.page_content}" for c in chunks_recuperados])
        
        print("✓ [ORQUESTADOR RAG] Marco normativo recuperado y mapeado al Estado.")
        return {"articulos_legales": contexto_ley}
