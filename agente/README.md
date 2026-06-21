# Sistema Multiagente PDF - Documentación

## Arquitectura General

El sistema está diseñado para procesar archivos PDF mediante un agente principal que evalúa reglas predefinidas en una base de datos (no acceso directo al PDF). Las reglas dictan qué subagentes especializados deben ser invocados en cada paso.

```
Interfaz Externa (CLI)
       ↓
   main.py (parsea args PDF + prompt)
       ↓
   MainAgent (inicia sesión en RuleEngine)
       ↓
   RuleEngine (BD de reglas, gestiona sesiones)
       ↓
   SubAgents (ejecutan tareas especializadas)
```

## Uso: Procesamiento de PDFs

### Opción 1: Ejecución desde CLI

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
- Iteraciones mostrando qué regla se ejecuta
- Invocaciones a subagentes
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
├── main.py                          # Punto de entrada (CLI)
├── config.yaml                      # Configuración de LLM
├── requirements.txt                 # Dependencias Python
├── data/
│   ├── rules.db                     # BD SQLite con reglas
│   └── sessions/                    # Estado persistido de sesiones
├── src/
│   ├── config.py                    # Utilidad de configuración
│   ├── utils/
│   │   └── pdf_reader.py            # Extractor de PDF a texto
│   ├── tools/
│   │   ├── rule_engine.py           # Motor de reglas (BD + sesiones)
│   │   └── rule_engine_cli.py       # CLI para gestionar reglas
│   └── agents/
│       ├── main_agent.py            # Agente principal (orquestador)
│       └── sub_agents.py            # Subagentes especializados
```

## Flujo de Ejecución

1. **Inicialización:**
   - Se carga `config.yaml` con datos del LLM
   - Se crea una instancia de `MainAgent`
   - Se inyecta el contexto del PDF y el prompt del usuario

2. **Sesión RuleEngine:**
   - El `MainAgent` llama a `rule_engine.start_session()`
   - RuleEngine crea un archivo JSON en `data/sessions/` para persistir el estado

3. **Loop Principal:**
   - Cada iteración solicita a RuleEngine: `get_next_rules(session_id)`
   - RuleEngine devuelve la próxima regla no ejecutada (ordenadas por prioridad)
   - El agente invoca el subagente asociado
   - Marca la regla como ejecutada: `mark_rule_executed(session_id, rule_id)`
   - Si hay una regla con action="stop", finaliza el loop

4. **Cierre:**
   - Llama a `rule_engine.close_session(session_id)`
   - El estado de la sesión persiste en disco para auditoría

## Ventajas Arquitectónicas

✓ **Determinismo:** Las reglas se evalúan desde una BD, no dependen del contexto del LLM.
✓ **Persistencia:** Cada sesión guarda su estado; se pueden auditar y reproducir.
✓ **Escalabilidad:** Nuevas reglas se agregan sin modificar código.
✓ **Desacoplamiento:** RuleEngine no accede al PDF; solo mantiene lógica de flujo.
✓ **Generalización:** Los PDFs vienen desde interfaz externa sin hardcodear paths.

## Próximos Pasos

1. Integrar llamadas a OpenAI/Anthropic en los subagentes
2. Pasar el contexto del PDF a los subagentes cuando sea necesario
3. Implementar más subagentes especializados según tu dominio
4. Crear una API REST wrapper (FastAPI) si necesitas exposición HTTP
