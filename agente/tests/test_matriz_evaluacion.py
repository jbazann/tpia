import os
import sys
import time
from src.agents.main_agent import MainAgent

# =====================================================================
# 1. ESCENARIOS DE LA MATRIZ DE EVALUACIÓN
# =====================================================================
scenarios = [
    {
        "id": "TC-HP-001-GRAFICA-EXITOSA",
        "tipo_medio": "grafica",
        "pdf_context_mock": "Gran Inauguración de la plataforma oficial de Casino Online Santa Fe. ¡Registrate hoy y empezá a jugar!",
        "analisis_visual_mock": (
            "Se observa al pie un zócalo horizontal continuo que ocupa el 12.5% de la altura total de la pieza gráfica. "
            "El OCR extrae las leyendas en caracteres negritas legibles: 'SOLO PARA MAYORES DE 18 AÑOS' y "
            "'EL JUGAR COMPULSIVAMENTE ES PERJUDICIAL PARA LA SALUD'. "
            "Al lado derecho se identifica el isologotipo institucional de la Lotería de Santa Fe."
        )
    },
    {
        "id": "TC-LM-003-RADIO-CON-MUSICA",
        "tipo_medio": "radial",
        "pdf_context_mock": (
            "Guión Técnico de Radio: [...] Descargá la app. [Acotación de producción]: Cortina musical de pop electrónico "
            "continúa sonando en volumen alto de fondo mientras el locutor enuncia rápidamente al final: "
            "'Solo para mayores de 18 años es un mensaje de Lotería de Santa Fe'."
        ),
        "analisis_visual_mock": "El PDF no contiene imágenes embebidas. El análisis visual no aplica."
    },
    {
        "id": "TC-LM-004-BANNER-HORIZONTAL-AMBIGUO",
        "tipo_medio": "grafica",
        "pdf_context_mock": "Santa Fe Apuestas Online Oficial.",
        "analisis_visual_mock": (
            "Se analiza una pieza de diseño marquesina rectangular de formato extremadamente alargado (relación de aspecto horizontal de 8:1). "
            "Se detecta al pie un zócalo que ocupa exactamente el 10.0% de la altura total del anuncio con tipografías legibles "
            "y el isologotipo institucional de la Lotería de Santa Fe."
        )
    },
    {
        "id": "TC-LM-005-OMISION-LEYENDA-SALUD",
        "tipo_medio": "grafica",
        "pdf_context_mock": "Jugá y ganá en las mesas de poker en vivo de Santa Fe.",
        "analisis_visual_mock": (
            "Se observa zócalo reglamentario del 15% de altura. El procesamiento OCR detecta únicamente el fragmento textual: "
            "'SOLO PARA MAYORES DE 18 AÑOS'. No se registra la presencia ni la tipografía de la frase complementaria "
            "sobre el juego compulsivo."
        )
    },
    {
        "id": "TC-AD-006-FUERA-DE-DOMINIO",
        "tipo_medio": "general",
        "pdf_context_mock": "Factura de Servicios de Energía Eléctrica. Liquidación del mes de mayo de 2026. Detalle de consumo residencial de kilowatts hora...",
        "analisis_visual_mock": (
            "Se visualizan gráficos estadísticos de barra sobre consumo histórico hogareño y cuadros de texto con tarifas impositivas comerciales. "
            "No se detectan marcas de casinos, enlaces de juego online ni simbología de apuestas."
        )
    }
]

# =====================================================================
# 2. MINI CLASE MOCK NATIVA PARA TRICKEAR A LANGGRAPH
# =====================================================================
class MockImageAgent:
    """Reemplazo controlado para el ImageAgent que asegura el retorno de un dict."""
    def __init__(self, config, pdf_path, respuesta_fija):
        self.respuesta_fija = respuesta_fija

    def __call__(self, state):
        print(f"[MOCK IMAGE AGENTE] Inyectando descripción visual simulada de forma segura.")
        # Devolvemos un diccionario real para que LangGraph no explote
        return {"analisis_visual": self.respuesta_fija}


# =====================================================================
# 3. RUNNER PRINCIPAL
# =====================================================================
def run_matrix_evaluation():
    print("===============================================================")
    print("🚀 EJECUTANDO BATERÍA DE EVALUACIÓN AUTOMÁTICA (MOCK TESTS)   ")
    print("===============================================================")
    
    config = {
        "llm": {
            "model": "llama-3.3-70b-versatile",
            "temperature": 0.1
        }
    }
    
    # Instanciamos el Agente Coordinador
    main_agent = MainAgent(config)
    
    # Guardamos una referencia al constructor original para restaurarlo después
    from src.agents.image_agent import ImageAgent
    import src.agents.main_agent
    
    for tc in scenarios:
        print(f"\n\n🧪 [{tc['id']}]")
        print(f" soporte/medio detectado : '{tc['tipo_medio']}'")
        print("-" * 65)
        
        # Interceptamos dinámicamente la clase ImageAgent justo antes de armar el grafo
        # Redefinimos el constructor para que use nuestro MockImageAgent con la respuesta de este caso
        src.agents.main_agent.ImageAgent = lambda cfg, path: MockImageAgent(cfg, path, tc["analisis_visual_mock"])
        
        try:
            # Ejecutamos el pipeline completo de auditoría
            main_agent.run(
                pdf_context=tc["pdf_context_mock"],
                tipo_medio=tc["tipo_medio"],
                pdf_path="tests/mock_doc.pdf"
            )
        except Exception as e:
            print(f"❌ Error durante la ejecución del caso {tc['id']}: {e}")
            
        print("-" * 65)
        time.sleep(1)  # Delay para respetar las cuotas de Groq
        
    # Restauramos la clase original por buenas prácticas
    src.agents.main_agent.ImageAgent = ImageAgent

if __name__ == "__main__":
    if "GROQ_API_KEY" not in os.environ:
        print("⚠ Advertencia: GROQ_API_KEY no detectada. Recordá setearla en PowerShell.")
    run_matrix_evaluation()