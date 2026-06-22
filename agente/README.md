# Sistema Multiagente PDF - Documentación

## Arquitectura General

El sistema está diseñado para procesar archivos PDF mediante un agente principal que evalúa reglas predefinidas en una base de datos SQLite. Las reglas dictan qué flujos y agentes especializados deben ser invocados en cada paso. La orquestación interna de tareas complejas se maneja mediante LangGraph.

El pipeline visual de imágenes y el RAG se integran directamente como nodos secuenciales antes del juicio legal final:

```
                  ┌────────────────────────────────────────┐
                  │          PDF de Campaña (UI)           │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │      MainAgent.run()      │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │        RuleEngine         │
                        │   (rules.db - SQLite)     │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
    ┌───────────────────────────────────────────────────────────────────┐
    │                     Flujo LangGraph Compilado                     │
    │                                                                   │
    │   ┌──────────────┐     ┌──────────────┐     ┌───────────────┐     │
    │   │  ImageAgent  │ ──> │   RAGAgent   │ ──> │LegalSpecialist│     │
    │   │ (OCR + LLaVA)│     │ (BM25+Dense) │     │  (Especialista│     │
    │   └──────────────┘     └──────────────┘     │    Legal)     │     │
    │                                             └───────┬───────┘     │
    │                                                     │             │
    │                                                     ▼             │
    │                                             ┌───────────────┐     │
    │                                             │ VerdictIssuer │     │
    │                                             │ (Emisor de    │     │
    │                                             │  Veredicto)   │     │
    │                                             └───────────────┘     │
    └─────────────────────────────────────────────────────┬─────────────┘
                                                          │
                                                          ▼
                                                ┌───────────────────┐
                                                │  Veredicto Final  │
                                                │ (APROBAR/RECHAZAR)│
                                                └───────────────────┘
```

---

## Componentes Principales

### 1. ImageAgent (Análisis Visual)
Extrae las imágenes embebidas en el PDF usando `pymupdf`. Aplica doble técnica de auditoría:
*   **OCR (`pytesseract`)**: Para extraer cualquier texto embebido en la gráfica o cartel.
*   **Modelo de Visión Multimodal (Groq/LLaMA 4 Scout)**: Evalúa visualmente la disposición de logos, la proporción del zócalo de advertencias (debe ser `>= 10%`) y la presencia de la marca de Lotería de Santa Fe.

### 2. RAGAgent (Marco Normativo)
Indexa los decretos y resoluciones oficiales en una base vectorial ChromaDB. Utiliza una estrategia híbrida:
*   **Dense Retrieval** (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`).
*   **Sparse Retrieval** (`BM25` de rango de palabras).
*   Ensemble Retriever para combinar ambos resultados en un único conjunto de leyes aplicables vigentes.

### 3. LegalSpecialist (Análisis Normativo)
LLM que actúa como inspector legal oficial. Contrasta la información combinada del texto del PDF y las imágenes audita contra las leyes devueltas por el RAG.

### 4. VerdictIssuer (Sentencia Estructurada)
Emite la resolución final limpia: `APROBAR`, `RECHAZAR` o `REVISAR`, junto con un resumen explicativo limitado a 3 oraciones.

---

## Uso y CLI

### Ejecución de Análisis
```bash
# Procesar un PDF y auditarlo automáticamente
python main.py -f "ruta/al/archivo.pdf"

# Procesar con instrucciones o prompts adicionales del usuario
python main.py -f "ruta/al/archivo.pdf" -p "Validar específicamente zócalos de vestimenta"
```

### Gestión de Reglas desde CLI
```bash
# Listar todas las reglas vigentes en rules.db
python -m src.tools.rule_engine_cli list

# Añadir una regla personalizada
python -m src.tools.rule_engine_cli add --name "check_fonts" --priority 10 --agent "font_checker"
```

---

## Ejecución de Tests Unitarios

Los tests están ubicados en `tests/test_agent.py` y verifican:
*   La correcta extracción y detección semántica del tipo de medio.
*   El ciclo de vida del `RuleEngine`, incluyendo base de datos transaccional SQLite temporal y la persistencia de estados de sesión.

Para ejecutar los tests:
```bash
cd agente
python -m unittest tests/test_agent.py
```
