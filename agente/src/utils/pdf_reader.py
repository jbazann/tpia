import os
import re

def read_pdf(file_path: str) -> str:
    """
    Extrae el texto de un archivo PDF usando pymupdf (fitz).
    Maneja correctamente PDFs con columnas, fuentes embebidas y layouts complejos.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo PDF '{file_path}' no existe.")

    if not file_path.lower().endswith('.pdf'):
        raise ValueError(f"El archivo '{file_path}' no es un PDF válido.")

    try:
        import fitz  # pymupdf
    except ImportError:
        raise ImportError(
            "pymupdf no está instalado. Ejecutá: pip install pymupdf"
        )

    try:
        doc = fitz.open(file_path)

        if len(doc) == 0:
            raise ValueError("El PDF no contiene páginas.")

        pages_text = []
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            if text and text.strip():
                pages_text.append(text)

        doc.close()

    except fitz.FileDataError as e:
        raise ValueError(f"El PDF está corrupto o no es válido: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error inesperado al procesar el PDF: {str(e)}")

    full_text = "\n".join(pages_text)

    if not full_text or full_text.strip() == "":
        raise ValueError(
            "El PDF no contiene texto extraíble. "
            "Puede ser un PDF escaneado sin OCR aplicado."
        )

    # Normalizar espaciado excesivo preservando saltos de párrafo
    full_text = re.sub(r'\n{3,}', '\n\n', full_text)
    full_text = re.sub(r' {2,}', ' ', full_text)

    return full_text.strip()


def detect_media_type(text: str) -> str:
    """
    Detecta el tipo de medio publicitario a partir del contenido del PDF
    para mejorar la precisión del retriever RAG.
    Retorna: 'grafica', 'radial', 'video', 'pnt', o 'general'.
    """
    text_lower = text.lower()

    if any(kw in text_lower for kw in ["radio", "radial", "spot radial", "locutor", "audio"]):
        return "radial"
    if any(kw in text_lower for kw in ["video", "televisión", "tv", "spot televisivo", "placa final"]):
        return "video"
    if any(kw in text_lower for kw in ["influencer", "periodista", "pnt", "no tradicional", "mención"]):
        return "pnt"
    if any(kw in text_lower for kw in ["gráfico", "gráfica", "aviso", "banner", "cartel", "vía pública", "zócalo"]):
        return "grafica"

    return "general"
