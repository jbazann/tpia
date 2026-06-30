# TPIA - Auditoría Publicitaria Multi-Agente

El proyecto implementa una arquitectura que combina una interfaz de usuario interactiva y un motor de inferencia de lenguaje natural basado en agentes para el procesamiento y control de normativas de material publicitario.

## 📂 Estructura del Proyecto

El sistema se divide en los siguientes módulos principales:

- **[`agente/`](./agente/)**: Aplicación Python multi-agente que se encarga del procesamiento de PDFs, validación de reglas e inferencia con IA. Incluye su propio [`README.md`](./agente/README.md) con detalles específicos del agente.
- **[`dashboard/`](./dashboard/)**: Interfaz de usuario construida con React (Frontend) y Go/Wails (Backend) que se comunica con el agente para operar el sistema. Incluye su propio [`README.md`](./dashboard/README.md).
- **`pruebas/`**: Directorio de pruebas y datos de validación del sistema.
- **`dist/`**: Carpeta donde se empaquetan los ejecutables listos para producción tras el proceso de build.

## 📚 Documentación

Se puede encontrar información detallada sobre distintos aspectos del proyecto en los siguientes documentos:

- 🏗️ **[Arquitectura del Sistema](SYSTEM_ARCHITECTURE.md)**: Detalles sobre el diseño técnico, el flujo de procesamiento distribuido local y la interacción entre el dashboard y el agente.
- 📖 **[Manual de Usuario](MANUAL_DE_USUARIO.md)**: Guía paso a paso sobre cómo utilizar el sistema de auditoría, configurar reglas normativas y analizar el material publicitario.
- 🛠️ **[Guía de Construcción (Build)](BUILD.md)**: Instrucciones detalladas y requisitos para compilar y empaquetar el dashboard y el agente en una distribución ejecutable.
- 📄 **[Informe de Entrega 2](INFORME_ENTREGA_2.md)**: Reporte y documentación complementaria correspondiente a la segunda entrega del proyecto.
