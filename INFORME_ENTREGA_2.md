# Trabajo Práctico N° 2: Diseño e Implementación de Agentes Inteligentes
## Informe Técnico de Avances - 2ª Entrega (22/06/2026)

**Curso:** Inteligencia Artificial (Año 2026)  
**Proyecto:** TPIA - Sistema Inteligente para Auditoría Normativa y Control Publicitario (Lotería de Santa Fe)

---

## 1. Descripción General del Problema y Caso de Uso
El control de la pauta publicitaria oficial y privada en la Lotería de Santa Fe es un proceso crítico que demanda verificar manualmente si las piezas promocionales (gráficas, radiales, televisivas, PNT) cumplen estrictamente con regulaciones legales (Anexo I de Resoluciones del Directorio). Esto incluye chequear de forma rigurosa la presencia y legibilidad de leyendas de advertencia obligatorias (ej: *"El jugar compulsivamente es perjudicial para la salud"*), la inclusión de logos institucionales y la proporción visual de zócalos informativos.

**TPIA** automatiza este proceso mediante un agente autónomo inteligente que percibe tanto el contenido textual como el visual del material publicitario, contrasta dicha información contra el marco legal y emite un dictamen vinculante.

---

## 2. Definición del Objetivo del Agente
El agente tiene como objetivo principal **auditar piezas publicitarias multiformato (cargadas en formato PDF) y emitir un veredicto definitivo (`APROBAR`, `RECHAZAR` o `REVISAR`)** justificando legalmente la decisión basándose en el contraste cruzado de las reglas provistas por el usuario y la normativa oficial recuperada.

---

## 3. Arquitectura del Agente: Módulos, Tecnologías y Workflow
El sistema cuenta con una arquitectura híbrida de **Orquestación por Motor de Reglas (SQLite)** y un **Grafo Acíclico Dirigido Multi-Agente (LangGraph)**.

```
  ┌────────────────────────────────────────────────────────┐
  │                    Dashboard UI (Wails)                │
  │     [React Frontend]   ◄──►   [Go Binder Backend]       │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼ (1. Invoca agente con PDF / 2. CRUD Reglas)
  ┌────────────────────────────────────────────────────────┐
  │                    Agente Orquestador                  │
  │                     (main.py / Python)                 │
  └───────────────────────────┬────────────────────────────┘
                              │
                              ▼ (Ejecuta flujo secuencial LangGraph)
  ┌────────────────────────────────────────────────────────┐
  │  ImageAgent  ➔  RAGAgent  ➔  LegalSpecialist  ➔  Verdict │
  │  (Visión)       (Leyes)      (Comparación)   (Firma)   │
  └────────────────────────────────────────────────────────┘
```

### Detalle de los Sub-Agentes en LangGraph:
1.  **ImageAgent (Percepción Visual):** Extrae imágenes del PDF usando `PyMuPDF` y las procesa con dos herramientas: OCR (`pytesseract`) y descripción semántica mediante un modelo multimodal en la nube (`meta-llama/llama-4-scout-17b-16e-instruct`).
2.  **RAGAgent (Percepción Contextual/Leyes):** Recupera leyes relevantes utilizando búsquedas vectoriales densas e indexación dispersa (BM25) sobre bases de datos locales indexadas en **ChromaDB**.
3.  **LegalSpecialist (Razonamiento y Contraste):** LLM principal que evalúa el contenido extraído (texto + reporte de visión) frente a las leyes recuperadas por RAG y la regla de negocio que se está ejecutando.
4.  **VerdictIssuer (Acción/Decisión):** Encargado de formatear la salida final y firmar con un veredicto estructurado.

---

## 4. Definición del Ambiente, Percepciones y Acciones (Tools)

### Ambiente:
*   **Tipo de Ambiente:** Parcialmente observable (el agente no sabe a priori qué contiene el PDF ni qué leyes aplican hasta recuperarlas), secuencial, estático y determinista en su orquestador de reglas.
*   **Fuentes de Entrada:** Archivos en formato PDF que representan campañas publicitarias gráficas, radiales o de video.
*   **Base de Conocimiento:** 
    *   Una base de datos SQLite (`rules.db`) para gestionar reglas personalizadas agregadas en vivo por el auditor.
    *   Una base vectorial `ChromaDB` con los artículos normativos oficiales de la Lotería de Santa Fe.

### Percepciones (Inputs del Agente):
1.  **Texto Crudo:** Extraído directamente del PDF.
2.  **Imágenes Embebidas:** Extraídas de forma binaria.
3.  **Leyes Recuperadas:** Artículos obtenidos mediante RAG.
4.  **Reglas de Usuario:** Reglas de control dinámicas inyectadas desde SQLite.

### Acciones / Tools Implementadas (Mínimo Obligatorio):
El agente cuenta con **3 herramientas principales (Tools)** funcionales escritas en Python:
1.  **`extract_images_from_pdf` (Manipulación de Archivos):** Extrae imágenes embebidas en formato binario de cada página del PDF utilizando la librería `pymupdf`.
2.  **`ocr_image` (Extracción de Texto Visual):** Recibe las imágenes y aplica OCR utilizando `pytesseract` y el motor local de Tesseract para extraer texto explícito de banners.
3.  **`describe_image_with_llm` (Visión Multimodal):** Utiliza la API de Groq con el modelo visual `meta-llama/llama-4-scout-17b-16e-instruct` para analizar elementos visuales como la presencia de logos, posicionamiento de leyendas y estimaciones de proporción.
4.  **`ChromaDB Hybrid Retriever` (RAG):** Recuperación híbrida (Embeddings `HuggingFaceBge` + BM25) para encontrar regulaciones basadas en el canal detectado en el PDF.

---

## 5. Manejo de Contexto, Memoria y Ambiente
*   **Memoria de Ejecución (Sesión):** Las interacciones del agente y su progreso a través de las reglas de control se gestionan a través de archivos de sesión JSON locales (`agente/data/sessions/<session_id>.json`).
*   **Transaccionalidad limpia:** El orquestador guarda en el JSON qué reglas de SQLite ya han sido procesadas (`executed_rules`) y el estado interno del análisis, lo que permite que el bucle de razonamiento sea reentrante y robusto. Las sesiones tienen un mecanismo automático de limpieza de basura (TTL) de 24 horas.

---

## 6. Logging Estructurado y Observabilidad (Cumplimiento de Consigna)
Para cumplir con el requerimiento de observabilidad paso a paso sin interferir en los canales IPC del backend, se diseñó e implementó:
1.  **TeeLogger Interceptor (Python):** Clase que duplica y redirige toda la salida estándar (`stdout` y `stderr`) del proceso Python a un archivo físico persistente: `agente/data/logs/agent_observability.log`.
2.  **Logging Estructurado de LLM y Tools:**
    *   Cada llamada de LLM registra de forma clara e identificable la estructura del prompt del sistema, del usuario, y la respuesta en bloques delimitados: `[LLM_CALL]` y `[LLM_RESPONSE]`.
    *   Cada llamada a herramienta del sistema registra sus parámetros y su salida en bloques: `[TOOL_CALL]` y `[TOOL_RESULT]`.
3.  **Consola en Vivo (React):** Un visor de texto enriquecido en la UI del Dashboard que lee este archivo y le permite al auditor ver el proceso cognitivo de la IA en tiempo real sin bloqueos de la interfaz.

---

## 7. Avances de Implementación (Segunda Entrega)
A fecha del **22/06/2026**, el esqueleto ejecutable y funcional está completamente desarrollado:
*   [x] Interfaz de escritorio interactiva funcional (React + Wails Go compiled).
*   [x] Integración de base de datos SQLite sin requerir dependencias CGO complejas.
*   [x] Flujo de agentes en LangGraph interactuando de forma secuencial.
*   [x] Conectores de ChromaDB y APIs externas de Groq configurados.
*   [x] Pipeline de logs estructurados visible desde la aplicación.
*   [x] 7 tests unitarios automatizados que verifican el extractor y el motor de reglas en aislamiento.
