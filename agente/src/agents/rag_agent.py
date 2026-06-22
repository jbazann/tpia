from src.agents.state import EstadoEvaluacion
from src.utils.rag_retriever import get_hybrid_retriever


class RAGAgent:
    """
    Sub-agente responsable de recuperar el marco normativo correspondiente
    según el tipo de medio detectado en el estado.
    """
    def __init__(self, config: dict):
        self.retriever = get_hybrid_retriever(config)

    def __call__(self, state: EstadoEvaluacion) -> dict:
        solicitud_id = state.get('solicitud_id', 'N/A')
        tipo_medio = state.get('tipo_medio', 'general')

        print(f"\n[ORQUESTADOR RAG] Evaluando solicitud {solicitud_id} | Medio detectado: '{tipo_medio}'")

        # Query semántica orientada al tipo de medio detectado automáticamente
        query_busqueda = f"Requisitos normativos para publicidad {tipo_medio} Lotería Santa Fe"

        print("\n" + "="*50)
        print("[TOOL_CALL] ChromaDB + BM25 Híbrido (RAG)")
        print(f"Query: {query_busqueda}")
        print("="*50 + "\n")

        chunks_recuperados = self.retriever.invoke(query_busqueda)

        print("\n" + "="*50)
        print("[TOOL_RESULT] ChromaDB + BM25 Híbrido (RAG)")
        print(f"Retrieved {len(chunks_recuperados)} chunks.")
        for idx, c in enumerate(chunks_recuperados):
            print(f"  Chunk {idx+1} Source: {c.metadata.get('titulo', 'N/A')}")
            print(f"  Content: {c.page_content[:150]}...")
        print("="*50 + "\n")

        if not chunks_recuperados:
            print("[ORQUESTADOR RAG] Advertencia: no se recuperaron chunks. Verificá la base ChromaDB.")
            return {"articulos_legales": "No se encontró normativa relevante para el tipo de medio indicado."}

        contexto_ley = "\n\n".join([
            f"[{c.metadata.get('titulo', 'Artículo')}]: {c.page_content}"
            for c in chunks_recuperados
        ])

        print(f"[ORQUESTADOR RAG] {len(chunks_recuperados)} fragmentos normativos recuperados.")
        return {"articulos_legales": contexto_ley}
