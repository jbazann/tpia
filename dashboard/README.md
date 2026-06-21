# TPIA Dashboard

Este es el dashboard y la interfaz de usuario gráfica del Sistema Multiagente para Análisis de PDFs, construido utilizando el framework Wails (React-TS + Go).

## Arquitectura de Integración

El dashboard actúa como el puente visual hacia la lógica de procesamiento de documentos del agente Python. La comunicación se realiza invocando el empaquetado del agente a través de la interfaz de comandos (`exec.Command` en Go).

Flujo de interacción:
1. El usuario carga un PDF y escribe un prompt en la interfaz (React).
2. El backend de Wails (Go) guarda el PDF en un directorio temporal.
3. El backend ejecuta `agente.exe` (o `main.py`) pasando el archivo y el prompt mediante parámetros de línea de comandos.
4. El backend captura el texto impreso por el agente y devuelve el estado al frontend para mostrar los resultados y el veredicto final.

## Desarrollo

Para ejecutar la aplicación en modo desarrollo, utiliza el comando:
```bash
wails dev
```
Esto lanzará un servidor de desarrollo de Vite que soporta recarga rápida (HMR) para el frontend, además de ejecutar los enlaces de Go.

## Compilación

Para generar el ejecutable de producción del dashboard, ejecuta:
```bash
wails build
```
El archivo final se ubicará en la carpeta `build/bin`.
