import os
import re
import yaml
from pathlib import Path
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ==========================================
# 1. CONTENIDO DE LA RESOLUCIÓN
# ==========================================
full_text = """
1. Publicidad Gráfica
Toda publicidad de casinos físicos y apuestas en línea difundidas a través de internet, plataformas de medios o redes sociales, cartelería en la vía pública, medios o plataformas de difusión gráfica, deberá incluir las leyendas "SOLO PARA MAYORES DE 18 AÑOS" Y "EL JUGAR COMPULSIVAMENTE ES PERJUDICIAL PARA LA SALUD", ambas en los términos establecidos en el presente, y junto al logo de LOTERÍA DE SANTA FE. Las leyendas establecidas, deberán ser proporcionadas dentro del espacio destinado a la pieza publicitaria, ocupando al pie de la misma, la totalidad de su espacio horizontal, y con una altura igual o mayor al 10% de la altura total del anuncio.

2. Publicidad radial
En publicidades emitidas por medios radiales, sólo será obligatoria la leyenda "SOLO PARA MAYORES DE 18 AÑOS ES UN MENSAJE DE LOTERÍA DE SANTA FE" que deberá estar al finalizar el anuncio, debiendo ser locutada en forma clara, sin música de fondo, audible y comprensible, no pudiendo ser la misma más veloz, en comparación con el texto locutado en el cuerpo principal del anuncio.

3. Publicidad por videos
Cuando la publicidad sea emitida en medios televisivos o digitales o de cualquier otro formato mediante la difusión de video el mismo deberá contener los anuncios conforme lo previsto en el punto 1 (publicidad gráfica) durante el tiempo que dure el video y, agregar al finalizar una placa con la imagen centrada de las leyendas y logo de Lotería de Santa Fe detallado en el punto 1.

4. Pauta no tradicional
La publicidad que se realice oralmente mediante P.N.T. o mediante influencers, actores o periodistas deberá finalizar con la leyenda prevista en el punto 2 en los términos allí previstos, o bien agregando las leyendas del punto 1 durante todo el tiempo que se esté haciendo alusión a la modalidad de participación Y/O acceso a los sitios de juegos y apuestas.

5. Publicidad en espacios alternativos
En aquellas publicidades gráficas que no sea posible la colocación del zócalo previsto en el punto 1 (por ejemplo camisetas o vestimenta en general), se deberá ubicar debajo de la marca de la empresa ocupando dos renglones la leyenda "SOLO PARA MAYORES DE 18 AÑOS" y junto a la misma el logo de LOTERÍA DE SANTA FE.

6. Otra publicidad
En caso que la publicidad no quede encuadrada en ninguno de los anteriores el operador deberá comunicarse previamente con Lotería de Santa Fe para conocer cómo debe realizar la propuesta.
"""

def load_config(base_dir=None):
    if base_dir is None:
        script_dir = Path(__file__).parent
        base_dir = script_dir.parent
    
    config_path = os.path.join(base_dir, 'config.yaml')
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main(base_dir=None):
    print("Iniciando ingesta de normativa...")
    config = load_config(base_dir)
    rag_config = config.get("rag", {})
    
    if base_dir is None:
        base_dir = Path(__file__).parent.parent
        
    db_path = os.path.join(base_dir, rag_config.get("db_path", "data/chroma_db"))
    collection_name = rag_config.get("collection_name", "normativa_publicidad")
    model_name = rag_config["embedding_model"]

    # ==========================================
    # 2. CHUNKING CONTROLADO POR PUNTOS NORMATIVOS
    # ==========================================
    # Separamos limpiamente usando los identificadores numéricos del documento real
    parts = re.split(r'(?=\n\s*\d+\.\s+)', full_text)
    parts = [p.strip() for p in parts if p.strip()]

    docs = []
    for p in parts:
        # Extraemos el número y la primera línea como título semántico
        lines = p.split('\n')
        header_line = lines[0]

        match_num = re.match(r'^(\d+)\.', header_line)
        art_num = int(match_num.group(1)) if match_num else 0

        docs.append(Document(
            page_content=p,
            metadata={'art': art_num, 'titulo': header_line}
        ))

    print(f"✓ {len(docs)} puntos normativos procesados y chunkedos.")

    # ==========================================
    # 3. GENERACIÓN DE EMBEDDINGS E INDEXACIÓN
    # ==========================================
    emb = HuggingFaceEmbeddings(model_name=model_name)

    # Guardamos en ChromaDB local de manera persistente
    vector_store = Chroma.from_documents(
        docs, 
        emb, 
        collection_name=collection_name, 
        persist_directory=db_path
    )
    print(f"✓ Chunks indexados con éxito en ChromaDB (Ruta: {db_path}).")

if __name__ == "__main__":
    main()
