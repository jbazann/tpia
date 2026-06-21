import os
from pathlib import Path
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever

def get_hybrid_retriever(config: dict):
    """
    Inicializa el EnsembleRetriever leyendo los documentos de ChromaDB persistente
    y devolviendo un pipeline híbrido (BM25 + Dense).
    """
    rag_config = config.get("rag", {})
    
    # Asegurar rutas relativas correctas
    project_root = Path(__file__).parent.parent.parent
    db_path = os.path.join(project_root, rag_config.get("db_path", "data/chroma_db"))
    collection_name = rag_config.get("collection_name", "normativa_publicidad")
    model_name = rag_config.get("embedding_model", "paraphrase-multilingual-MiniLM-L12-v2")
    k_val = rag_config.get("k", 3)

    if not os.path.exists(db_path):
        raise FileNotFoundError(f"No se encontró la base de datos RAG en {db_path}. Ejecuta scripts/init_rag_db.py primero.")

    emb = HuggingFaceEmbeddings(model_name=model_name)
    
    # Cargamos el vector store
    vector_store = Chroma(
        collection_name=collection_name, 
        embedding_function=emb,
        persist_directory=db_path
    )
    
    dense_retriever = vector_store.as_retriever(search_kwargs={'k': k_val})
    
    # Para BM25 necesitamos los documentos. Podemos obtenerlos de Chroma.
    # Obtenemos todos los documentos. Para colecciones pequeñas es perfectamente válido.
    all_docs = vector_store.get(include=["documents", "metadatas"])
    
    from langchain_core.documents import Document
    docs = []
    for i in range(len(all_docs['ids'])):
        docs.append(Document(
            page_content=all_docs['documents'][i],
            metadata=all_docs['metadatas'][i]
        ))
        
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = k_val
    
    # Fusión híbrida estable
    hybrid_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, dense_retriever],
        weights=[0.5, 0.5]
    )
    
    return hybrid_retriever
