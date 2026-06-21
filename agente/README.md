# Sistema Multiagente PDF - Documentación

## Arquitectura General

El sistema está diseñado para procesar archivos PDF mediante un agente principal que evalúa reglas predefinidas en una base de datos (no acceso directo al PDF). Las reglas dictan qué flujos y agentes especializados deben ser invocados en cada paso. La orquestación interna de tareas complejas se maneja mediante LangGraph.

```
Interfaz Externa (Dashboard en Wails o CLI)
       ↓
   main.py (parsea args PDF + prompt)
       ↓
   MainAgent (inicia sesión en RuleEngine)
       ↓
   RuleEngine (BD de reglas, gestiona sesiones)
       ↓
   Flujo LangGraph (RAG -> Legal Specialist -> Verdict Issuer)
```

## Uso: Procesamiento de PDFs

### Ejecución desde CLI

```bash
# Procesar un PDF sin instrucción específica
python main.py -f "ruta/al/archivo.pdf"

# Procesar un PDF con instrucción específica
python main.py --file "ruta/al/archivo.pdf" --prompt "Extrae las entidades de persona mencionadas"

# Ver ayuda
python main.py -h
```

**Salida esperada:**
- Sesión iniciada en RuleEngine
- Ejecución del flujo de LangGraph mostrando iteraciones (RAG, Especialista Legal, Veredicto)
- Impresión del veredicto y justificación final en consola (capturado por el Dashboard)
- Estado persistido en `data/sessions/`
- Sesión cerrada correctamente

## Gestión de Reglas

### Comando: Listar reglas disponibles

```bash
python -m src.tools.rule_engine_cli list
```

Muestra todas las reglas en la BD, su prioridad, agentes asociados y estado.

### Comando: Agregar una nueva regla

```bash
python -m src.tools.rule_engine_cli add \
  --name "mi_regla" \
  --priority 5 \
  --agent "custom_agent" \
  --type "invoke_subagent" \
  --payload "Descripción de la acción"
```

**Parámetros:**
- `--name`: Nombre único de la regla
- `--priority`: Número entero (menor = mayor prioridad)
- `--agent`: Nombre del subagente a invocar
- `--type`: Tipo de acción (`invoke_subagent` o `stop`)
- `--payload`: Descripción/instrucción para el subagente

### Comando: Listar sesiones

```bash
python -m src.tools.rule_engine_cli list-sessions
```

Muestra el historial de sesiones procesadas con sus timestamps y estado.

## Estructura de Carpetas

```
p:\tpia/
├── dashboard/                       # UI Gráfica en Wails/React
├── agente/
│   ├── main.py                      # Punto de entrada y parser CLI
│   ├── config.yaml                  # Configuración de LLM
│   ├── requirements.txt             # Dependencias Python
│   ├── agente.spec                  # Configuración de empaquetado PyInstaller
│   ├── data/
│   │   ├── rules.db                 # BD SQLite con reglas
│   │   └── sessions/                # Estado persistido de sesiones
│   └── src/
│       ├── config.py                # Utilidad de configuración
│       ├── utils/
│       │   ├── pdf_reader.py        # Extractor de PDF a texto
│       │   └── rag_retriever.py     # Utilidad de búsqueda RAG
│       ├── tools/
│       │   ├── rule_engine.py       # Motor de reglas (BD + sesiones)
│       │   └── rule_engine_cli.py   # CLI para gestionar reglas
│       └── agents/
│           ├── main_agent.py        # Agente principal (orquestador general)
│           ├── state.py             # Definiciones de estado para LangGraph
│           ├── rag_agent.py         # Nodo LangGraph: Recuperación
│           ├── legal_specialist.py  # Nodo LangGraph: Especialista Legal
│           └── verdict_issuer.py    # Nodo LangGraph: Emisor de Veredicto
```

## Flujo de Ejecución

1. **Inicialización:**
   - Se carga `config.yaml` con datos del LLM.
   - Se crea una instancia de `MainAgent` que a su vez compila el grafo de LangGraph.
   - Se inyecta el contexto del PDF y el prompt del usuario.

2. **Sesión RuleEngine:**
   - El `MainAgent` llama a `rule_engine.start_session()`.
   - RuleEngine crea un archivo JSON en `data/sessions/` para persistir el estado.

3. **Loop Principal (MainAgent + LangGraph):**
   - El agente solicita a RuleEngine: `get_next_rules(session_id)`.
   - Si la regla invoca `legal_evaluation_flow`, el `MainAgent` dispara la ejecución del grafo compilado de LangGraph.
   - El estado viaja secuencialmente por RAG, Legal Specialist y Verdict Issuer, procesando el contexto.
   - Se imprime el resultado y se marca la regla como ejecutada.
   - Si hay una regla con action="stop", finaliza el loop.

4. **Cierre:**
   - Llama a `rule_engine.close_session(session_id)`.
   - El estado de la sesión persiste en disco para auditoría.
   - Retorna los resultados de consola, los cuales son leídos por el Dashboard.

## Ventajas Arquitectónicas

✓ **Determinismo:** El flujo general está guiado por la BD (RuleEngine) y LangGraph permite transiciones precisas.
✓ **Persistencia:** Cada sesión guarda su estado; se pueden auditar y reproducir.
✓ **Integración Completa:** Se provee una CLI sólida que conecta perfectamente con el frontend del Dashboard.
✓ **Desacoplamiento:** El Motor de Reglas mantiene la lógica de control separada de la ejecución de LLMs.

## Próximos Pasos

1. Mejorar el refinamiento de RAG utilizando embeddings vectoriales (vectorstore) persistentes.
2. Añadir nuevos flujos de LangGraph para procesar diferentes tipos de documentos (ej. facturas o reportes médicos).
3. Expandir la comunicación entre el Agente y el Dashboard a formatos estructurados (ej. JSON puro vía stdout) para facilitar parseos en la UI.
