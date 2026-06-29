import os
import base64
import tempfile
from pathlib import Path
from typing import Optional


def extract_images_from_pdf(pdf_path: str) -> list[dict]:
    """
    Extrae todas las imágenes de un PDF usando pymupdf.
    Retorna una lista de dicts con la imagen en base64 y metadata de página.
    """
    try:
        import fitz
    except ImportError:
        raise ImportError("pymupdf no está instalado. Ejecutá: pip install pymupdf")

    doc = fitz.open(pdf_path)
    images = []

    for page_num, page in enumerate(doc):
        image_list = page.get_images(full=True)
        for img_index, img_info in enumerate(image_list):
            xref = img_info[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]  # "png", "jpeg", etc.

                images.append({
                    "page": page_num + 1,
                    "index": img_index,
                    "ext": ext,
                    "data_b64": base64.b64encode(image_bytes).decode("utf-8"),
                    "size_bytes": len(image_bytes),
                })
            except Exception as e:
                print(f"[ImageTools] No se pudo extraer imagen xref={xref} en página {page_num + 1}: {e}")

    doc.close()
    print(f"[ImageTools] {len(images)} imagen(es) extraída(s) del PDF.")
    return images


def ocr_image(image_b64: str, ext: str = "png") -> str:
    """
    Aplica OCR sobre una imagen en base64 usando pytesseract.
    Si pytesseract no está disponible, retorna cadena vacía con advertencia.
    """
    try:
        import pytesseract
        from PIL import Image
        import io
    except ImportError:
        print("[ImageTools] pytesseract/Pillow no disponibles. Saltando OCR.")
        return ""

    try:
        img_bytes = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(img_bytes))
        
        print("\n" + "="*50)
        print("[TOOL_CALL] pytesseract - OCR Extraction")
        print(f"Input image dimensions: {image.size} | Format: {image.format}")
        print("="*50 + "\n")

        # lang='spa' para español; fallback a 'eng' si no está el paquete de idioma
        try:
            text = pytesseract.image_to_string(image, lang="spa")
        except pytesseract.TesseractError:
            text = pytesseract.image_to_string(image, lang="eng")
        
        print("\n" + "="*50)
        print("[TOOL_RESULT] pytesseract - OCR Extraction")
        print(f"Result text size: {len(text)} characters")
        print(f"Text preview: {text.strip()[:150]}...")
        print("="*50 + "\n")
        
        return text.strip()
    except Exception as e:
        print(f"[ImageTools] Error en OCR: {e}")
        return ""


def describe_image_with_llm(image_b64: str, ext: str, groq_api_key: str, model: str) -> str:
    """
    Describe el contenido visual de una imagen usando un modelo multimodal vía Groq.
    Retorna una descripción semántica enfocada en elementos de publicidad normativa:
    logos, leyendas, zócalos, advertencias, etc.
    """
    try:
        from groq import Groq
    except ImportError:
        raise ImportError("groq SDK no instalado. Ejecutá: pip install groq")

    client = Groq(api_key=groq_api_key)

    # Formato data URI para la API
    mime_map = {"png": "image/png", "jpeg": "image/jpeg", "jpg": "image/jpeg", "webp": "image/webp"}
    mime_type = mime_map.get(ext.lower(), "image/png")
    data_uri = f"data:{mime_type};base64,{image_b64}"

    system_prompt = """\
Sos un auditor visual especializado en cumplimiento normativo publicitario de la Lotería de Santa Fe.
Analizá la imagen y describí en detalle:
- Presencia y posición de leyendas de advertencia ("SOLO PARA MAYORES DE 18 AÑOS", "EL JUGAR COMPULSIVAMENTE ES PERJUDICIAL PARA LA SALUD")
- Presencia del logo de Lotería de Santa Fe
- Proporción estimada del zócalo respecto al total de la imagen (si aplica)
- Texto visible en la imagen y su legibilidad
- Cualquier elemento visual relevante para la auditoría normativa
Sé conciso y técnico."""

    try:
        print("\n" + "="*50)
        print("[TOOL_CALL] Groq Multimodal Vision (LLaVA)")
        print(f"Model: {model}")
        print(f"Input: Image base64 data (Size: {len(image_b64)} chars) | Ext: {ext}")
        print("="*50 + "\n")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": system_prompt},
                        {"type": "image_url", "image_url": {"url": data_uri}},
                    ],
                }
            ],
            max_tokens=512,
        )
        result = response.choices[0].message.content.strip()

        print("\n" + "="*50)
        print("[TOOL_RESULT] Groq Multimodal Vision (LLaVA)")
        print(f"Result: {result[:200]}...")
        print("="*50 + "\n")

        return result
    except Exception as e:
        print(f"[ImageTools] Error en descripción semántica: {e}")
        return f"No se pudo analizar la imagen: {str(e)}"


def analyze_pdf_images(pdf_path: str, groq_api_key: str, model: str) -> str:
    """
    Pipeline completo de análisis visual de un PDF:
    1. Extrae imágenes
    2. Aplica OCR en cada imagen
    3. Genera descripción semántica con LLM multimodal
    Retorna un informe consolidado de todas las imágenes.
    """
    images = extract_images_from_pdf(pdf_path)

    if not images:
        return "El PDF no contiene imágenes embebidas. El análisis visual no aplica."

    reports = []
    for img in images:
        page = img["page"]
        ext = img["ext"]
        b64 = img["data_b64"]

        print(f"[ImageTools] Analizando imagen en página {page}...")

        # OCR: texto en la imagen
        ocr_text = ocr_image(b64, ext)

        # Descripción semántica con LLM multimodal
        semantic_desc = describe_image_with_llm(b64, ext, groq_api_key, model)

        report = f"--- Imagen en Página {page} ---\n"
        if ocr_text:
            report += f"[OCR] Texto detectado:\n{ocr_text}\n\n"
        report += f"[Análisis Visual]:\n{semantic_desc}\n"
        reports.append(report)

    return "\n".join(reports)
