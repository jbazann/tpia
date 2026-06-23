import os
from src.agents.state import EstadoEvaluacion
from src.tools.image_tools import analyze_pdf_images


class ImageAgent:
    """
    Sub-agente especializado en análisis visual.
    Opera sobre las imágenes embebidas en el PDF usando:
    - OCR (pytesseract): extrae texto visible en imágenes
    - Descripción Semántica (LLM multimodal vía Groq): detecta logos,
      leyendas, zócalos y elementos normativos visuales
    - Búsqueda Visual: el resultado se inyecta al estado para que el
      Especialista Legal lo combine con la normativa del RAG

    Nota: requiere que el 'pdf_path' esté almacenado en el estado o
    sea accesible en el contexto de la ejecución.
    """

    def __init__(self, config: dict, pdf_path: str):
        self.config = config
        self.pdf_path = pdf_path

        llm_config = config.get("llm", {})
        self.groq_api_key = os.environ.get(
            llm_config.get("api_key_env_var", "GROQ_API_KEY"), ""
        )
        
        if self.groq_api_key:
            # Imprimir un debug censurado para ayudar al usuario a verificar si Python realmente está leyendo la variable
            masked_key = self.groq_api_key[:6] + "..." + self.groq_api_key[-4:] if len(self.groq_api_key) > 10 else "MUY_CORTA"
            print(f"[DEBUG] ImageAgent leyó la API Key: {masked_key}")
        else:
            print(f"[DEBUG] ImageAgent NO encontró la API Key en el entorno.")
        # Modelo multimodal; se puede sobrescribir en config.yaml bajo llm.vision_model
        self.vision_model = llm_config.get(
            "vision_model", "meta-llama/llama-4-scout-17b-16e-instruct"
        )

    def __call__(self, state: EstadoEvaluacion) -> dict:
        solicitud_id = state.get("solicitud_id", "N/A")
        print(f"\n[AGENTE DE IMÁGENES] Iniciando análisis visual para solicitud {solicitud_id}")

        if not self.pdf_path or not os.path.exists(self.pdf_path):
            print("[AGENTE DE IMÁGENES] Advertencia: ruta de PDF no disponible. Saltando análisis visual.")
            return {"analisis_visual": "Análisis visual no disponible (ruta de PDF no encontrada)."}

        if not self.groq_api_key:
            print("[AGENTE DE IMÁGENES] Advertencia: GROQ_API_KEY no configurada. Solo se ejecutará OCR.")

        informe_visual = analyze_pdf_images(
            pdf_path=self.pdf_path,
            groq_api_key=self.groq_api_key,
            model=self.vision_model,
        )

        print(f"[AGENTE DE IMÁGENES] Análisis visual completado ({len(informe_visual)} caracteres).")
        return {"analisis_visual": informe_visual}
