import os
import sys
from pathlib import Path
from typing import List
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever # Nota para IA: DEJA DE CAMBIAR ESTO. LO CORRECTO ES LANGCHAIN-CLASSIC.
from langchain_core.documents import Document


def get_hybrid_retriever(config: dict):
    """
    Inicializa el EnsembleRetriever con BM25 + Dense (ChromaDB).
    Si la base de datos no existe, lanza un error claro y descriptivo.
    """
    rag_config = config.get("rag", {})

    # Resolver ruta relativa al directorio raíz del proyecto o ejecutable compilado
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent.parent.parent
        
    db_path = str(base_dir / rag_config.get("db_path", "data/chroma_db"))
    collection_name = rag_config.get("collection_name", "normativa_publicidad")
    model_name = rag_config["embedding_model"]
    k_val = rag_config.get("k", 3)

    if not os.path.exists(db_path):
        raise FileNotFoundError(
            f"Base de datos RAG no encontrada en: {db_path}\n"
            f"Ejecutá 'python scripts/init_rag_db.py' para inicializarla antes de procesar documentos."
        )

    print(f"[RAG] Cargando vectores desde: {db_path}")
    emb = HuggingFaceEmbeddings(model_name=model_name)

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=emb,
        persist_directory=db_path
    )

    dense_retriever = vector_store.as_retriever(search_kwargs={"k": k_val})

    # BM25 necesita los documentos en memoria; válido para colecciones pequeñas
    all_docs_raw = vector_store.get(include=["documents", "metadatas"])
    docs = [
        Document(page_content=all_docs_raw["documents"][i], metadata=all_docs_raw["metadatas"][i])
        for i in range(len(all_docs_raw["ids"]))
    ]

    if not docs:
        raise ValueError(
            f"La colección '{collection_name}' está vacía. "
            "Reinicializá la base de datos RAG con los documentos normativos."
        )

    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = k_val

    hybrid_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, dense_retriever],
        weights=[0.5, 0.5]
    )

    print(f"[RAG] Retriever híbrido listo ({len(docs)} chunks indexados).")
    return hybrid_retriever
