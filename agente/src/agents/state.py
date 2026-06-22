from typing import TypedDict

class EstadoEvaluacion(TypedDict, total=False):
    """
    Estado compartido que se transfiere entre los diferentes nodos 
    del LangGraph durante la evaluación legal.
    """
    solicitud_id: str             # Identificador de la solicitud
    tipo_medio: str               # "grafica", "radial", "video", "pnt", etc.
    archivo_contenido: str        # Transcripción del PDF o contenido a evaluar
    articulos_legales: str        # Contexto dinámico inyectado desde el RAG
    reporte_especialista: str     # Informe analítico en Lenguaje Natural del sub-agente
    veredicto_final: str          # APROBAR, RECHAZAR o REVISAR
    justificacion_final: str      # Síntesis estructurada para el veredicto
    regla_actual: dict            # Regla que se está evaluando en la iteración actual
