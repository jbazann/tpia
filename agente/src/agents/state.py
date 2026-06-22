from typing import TypedDict


class EstadoEvaluacion(TypedDict):
    """
    Estado compartido que se transfiere entre los nodos del grafo LangGraph.
    Incluye tanto el análisis de texto como el análisis visual de imágenes.
    """
    solicitud_id:        str   # Identificador único de la solicitud
    tipo_medio:          str   # "grafica", "radial", "video", "pnt", "general"
    archivo_contenido:   str   # Texto extraído del PDF
    analisis_visual:     str   # Informe del Agente de Imágenes (OCR + descripción semántica)
    articulos_legales:   str   # Normativa recuperada por el RAG
    reporte_especialista: str  # Informe analítico del Especialista Legal
    veredicto_final:     str   # "APROBAR", "RECHAZAR" o "REVISAR"
    justificacion_final: str   # Dictamen estructurado del Emisor de Veredicto
    regla_nombre:        str   # Nombre de la regla actual que se evalúa (Canal / Medio)
    regla_requisito:     str   # Especificaciones de la regla actual
