# TPIA - Documento de Arquitectura de Sistema

Este documento describe la arquitectura técnica del sistema de auditoría publicitaria **TPIA** desarrollado en colaboración con la UTN y Lotería de Santa Fe.

---

## 🏗️ Visión General del Sistema

El sistema implementa una arquitectura híbrida de **Procesamiento Distribuido Local** y **Servicios de Inferencia de Lenguaje Natural**:

```
 ┌──────────────────────────────────────────────┐
 │             Dashboard (Wails UI)             │
 │  React (Frontend) ◄──► Go Binder (Backend)   │
 └──────────────────────┬───────────────────────┘
                        │
                        │ 1. Invoca subproceso (main.py / agente.exe)
                        │ 2. Lee/Escribe reglas (SQLite Direct Connection)
                        ▼
 ┌──────────────────────────────────────────────┐
 │                Agente Python                 │
 │       Orquestador General & LangGraph        │
 └──────────────────────┬───────────────────────┘
                        │
      ┌─────────────────┴─────────────────┐
      ▼                                   ▼
 ┌──────────────┐                  ┌──────────────┐
 │  BDD Reglas  │                  │   BDD RAG    │
 │  (rules.db)  │                  │ (ChromaDB)   │
 └──────────────┘                  └──────────────┘
```

---

## 🛠️ Detalle de Componentes

### 1. Interfaz de Usuario (Dashboard)
*   **Frontend**: Desarrollado en **React** y **TypeScript**. Incorpora un panel interactivo para el control en tiempo real de las reglas en la base de datos, un visor de la línea de tiempo de observabilidad de LangGraph, una consola de logs simulada y drag & drop de archivos.
*   **Backend (Go/Wails)**: Expone bindings para que el frontend pueda interactuar con el sistema operativo de forma nativa. Esto incluye el guardado temporal de archivos subidos y la persistencia de reglas directamente en SQLite mediante `modernc.org/sqlite` (sin requerir CGO).

### 2. Motor de Control (RuleEngine)
*   Usa una base de datos **SQLite** (`rules.db`) que se inicializa en blanco para que los usuarios institucionales la gestionen a través de la UI.
*   En tiempo de ejecución, el Orquestador inyecta dinámicamente cada regla activa (Nombre y Requisitos) dentro del contexto del sistema de subagentes para realizar una validación técnica específica.
*   Controla el ciclo de vida de la sesión almacenando metadatos en archivos JSON con un TTL de 24 horas para autolimpieza de almacenamiento.

### 3. Orquestador Multi-Agente (LangGraph)
Encapsula la lógica recursiva del análisis en un flujo acíclico dirigido (DAG) compuesto por 4 sub-agentes independientes:

```
[Inicio] ──> ImageAgent ──> RAGAgent ──> LegalSpecialist ──> VerdictIssuer ──> [Fin]
```

1.  **ImageAgent (Análisis Visual)**:
    *   **Herramienta OCR (pytesseract)**: Lee texto explícito en imágenes.
    *   **Herramienta de Visión Multimodal (meta-llama/llama-4-scout-17b-16e-instruct)**: Analiza tamaños relativos, posicionamiento de logos y cumplimiento estético de los banners publicitarios.
2.  **RAGAgent (Búsqueda Normativa)**:
    *   Recupera normativa legal mediante embeddings vectoriales (dense retrieval) y concordancia exacta de palabras (sparse BM25) sobre una base de datos local **ChromaDB**.
3.  **LegalSpecialist (Juicio Técnico)**:
    *   LLM que unifica el texto extraído del PDF, la descripción visual del ImageAgent y contrasta exhaustivamente contra la legislación recuperada **y la regla dinámica provista** en ese ciclo.
4.  **VerdictIssuer (Firma de Dictamen)**:
    *   Filtra y emite la sentencia definitiva (`APROBAR`, `RECHAZAR` o `REVISAR`) utilizando formatos y directivas estrictas.

### 4. Trazabilidad y Observabilidad
*   **Persistencia de Logs (TeeLogger)**: Todo el output por consola del Orquestador y LangGraph (stdout y stderr) es interceptado nativamente en Python por la clase `TeeLogger` y persistido asíncronamente en el archivo plano rotativo `agente/data/logs/agent_observability.log`.
*   **Consumo Transparente UI**: El backend en Go localiza este archivo mediante bindings y lo transmite a un componente de "Consola en Vivo" en el React frontend, permitiendo la visualización limpia y sin bloqueo del ciclo de evaluación sin depender del pipeline IPC del sistema operativo.

---

## 📦 Flujo de Compilación y Distribución

El script `build.ps1` orquesta las tareas de construcción para generar binarios autocontenidos y listos para producción:

1.  **Compilación del Agente (PyInstaller)**:
    *   Empaqueta el runtime de Python, librerías y dependencias (como `pymupdf` y `langchain`) en un único binario independiente (`agente.exe`).
2.  **Compilación del Dashboard (Wails CLI)**:
    *   Empaqueta los recursos compilados de React (Vite HTML/JS) dentro del código nativo de Go, produciendo `dashboard.exe`.
3.  **Empaquetado de Distribución**:
    *   Consolida los artefactos en la carpeta `dist/`, la cual contiene:
        *   `dashboard.exe` (Ejecutable principal)
        *   `agente.exe` (Agente secundario)
        *   `config.yaml` (Variables del RAG y LLM)
