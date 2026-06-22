# Manual de Usuario - Auditoría Publicitaria Multi-Agente (TPIA)

Este documento explica cómo utilizar el sistema de auditoría publicitaria para la **Lotería de Santa Fe**. El sistema está diseñado para que un analista pueda configurar sus criterios de control, subir materiales publicitarios y obtener un dictamen normativo automatizado, con completa trazabilidad del proceso.

---

## 🚀 Flujo de Trabajo Paso a Paso

### 1. Configuración de Reglas (Pestaña "Reglas de Auditoría")
El sistema arranca con una base de conocimientos en blanco en cuanto a los parámetros específicos de auditoría. Tu primer paso es definir qué se debe controlar.

1.  Dirígete a la pestaña **Reglas de Auditoría** en el menú izquierdo.
2.  **Canal / Medio:** Escribe el nombre del canal publicitario o el nombre de la regla (Ej: *"Publicidad Gráfica"* o *"Control de PNT"*).
3.  **Requisitos / Especificaciones:** Detalla exactamente qué quieres que la Inteligencia Artificial valide. 
    *   *Ejemplo: "El zócalo de advertencia sobre jugar compulsivamente debe ocupar al menos el 10% del alto total del aviso y estar posicionado en el margen inferior."*
4.  Haz clic en **Agregar Regla**. Puedes agregar tantas reglas como consideres necesarias. Puedes activar, desactivar o eliminar estas reglas en la tabla inferior según tus necesidades.

> **💡 Importante:** El Orquestador de Inteligencia Artificial leerá estas reglas de forma dinámica durante la auditoría. ¡Sé lo más específico posible!

---

### 2. Subida y Auditoría (Pestaña "Procesamiento")
Una vez que las reglas están cargadas, es momento de subir el archivo PDF con la propuesta de la agencia de publicidad.

1.  Dirígete a la pestaña **Procesamiento**.
2.  Arrastra un archivo PDF al área punteada que dice **"Arrastra y suelta tu documento de campaña aquí"** (o haz clic para abrir el explorador de archivos).
3.  El sistema cargará el archivo y comenzará el análisis automáticamente. El estado del archivo pasará a "En Proceso".

Durante esta fase, ocurre la auditoría multi-agente en segundo plano:
*   **Visión e Imágenes:** El sistema extrae el texto y "mira" las imágenes del PDF para ubicar logos, tamaños y estructuras visuales.
*   **Leyes Vigentes:** El sistema busca en su base de datos legal interna (RAG) los artículos normativos de la Lotería de Santa Fe correspondientes al medio detectado.
*   **Evaluación:** Un Especialista Legal de IA contrasta las reglas que tú configuraste en el paso 1 contra el contenido del PDF y las leyes encontradas.

---

### 3. Trazabilidad en Tiempo Real (Pestaña "Observabilidad")
Si quieres ver qué está "pensando" o analizando la inteligencia artificial en tiempo real mientras evalúa el PDF, puedes consultar la terminal de logs.

1.  Dirígete a la pestaña **Observabilidad**.
2.  Haz clic en el botón **Actualizar Logs**.
3.  Podrás ver una consola de texto oscuro que te mostrará los pasos internos del modelo, qué imágenes encontró, qué leyes está leyendo y cómo está aplicando tus reglas de auditoría.

---

### 4. Veredicto y Dictamen Final
Una vez que el procesamiento termina, vuelve a la pestaña **Procesamiento**.

1.  El estado del archivo pasará a **Procesado**.
2.  Se desplegará una tarjeta de **Resultado de Evaluación Legal** mostrando el veredicto definitivo:
    *   🟢 **APROBAR**: La publicidad cumple todas las normativas y tus reglas configuradas.
    *   🔴 **RECHAZAR**: Se encontraron infracciones y la publicidad no es apta.
    *   🟡 **REVISAR**: El sistema requiere la mirada de un humano para tomar la decisión final debido a ambigüedades.
3.  Debajo del veredicto, leerás el **Dictamen Técnico** estructurado con la lista exacta de violaciones normativas detectadas, listo para ser copiado y enviado a la agencia de publicidad para su corrección.
