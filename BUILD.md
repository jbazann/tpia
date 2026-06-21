# TPIA - Dashboard Build Guide

## Build del Proyecto Completo

El proyecto está compuesto por dos módulos:
- **agente**: Aplicación Python multi-agente para procesamiento de PDFs
- **dashboard**: Interfaz Go/Wails que invoca el agente

El script de build empaqueta ambos en una distribución lista para producción.

## Requisitos Previos

### Windows
- **Python 3.8+** - [Descargar](https://www.python.org/downloads/)
  - Asegúrate de agregar Python al PATH durante la instalación
- **Go 1.20+** - [Descargar](https://golang.org/dl/)
- **Node.js 16+** - [Descargar](https://nodejs.org/)
- **Wails 2.7+** - Instalar con: `go install github.com/wailsapp/wails/v2/cmd/wails@latest`

### macOS/Linux
```bash
# macOS
brew install python go node wails

# Linux (Ubuntu/Debian)
sudo apt-get install python3 golang-go nodejs npm
go install github.com/wailsapp/wails/v2/cmd/wails@latest
```

## Construir el Proyecto

### Opción 1: Script Batch (Windows Recomendado)

```batch
cd p:\tpia
build.bat [release|debug] [--skip-agent] [--skip-dashboard]
```

Ejemplos:
```batch
build.bat                    # Build completo en modo release (por defecto)
build.bat debug             # Build completo en modo debug
build.bat --skip-agent      # Build solo del dashboard (reutiliza agente existente)
build.bat --skip-dashboard  # Build solo del agente
```

### Opción 2: Script PowerShell (Windows)

```powershell
cd p:\tpia
.\build.ps1 -BuildType release
.\build.ps1 -BuildType debug -SkipAgentBuild
```

### Opción 3: Manual

#### Paso 1: Construir el Agente Python

```bash
cd p:\tpia\agente

# Instalar dependencias
pip install -r requirements.txt

# Instalar PyInstaller
pip install pyinstaller

# Empaquetar con PyInstaller
pyinstaller --name agente ^
    --onefile ^
    --hidden-import=PyPDF2 ^
    --hidden-import=pyyaml ^
    --hidden-import=python-dotenv ^
    --hidden-import=openai ^
    --hidden-import=tabulate ^
    --add-data "config.yaml:." ^
    main.py
```

El ejecutable estará en: `dist/agente.exe`

#### Paso 2: Copiar Agente al Dashboard

```bash
# Copiar desde p:\tpia\agente\dist\agente.exe a p:\tpia\dashboard\resources\agente.exe
```

#### Paso 3: Construir el Dashboard

```bash
cd p:\tpia\dashboard

# Instalar dependencias del frontend
cd frontend
npm install
cd ..

# Build con Wails
wails build -webpackdir "./frontend"
```

El ejecutable estará en: `build/bin/dashboard.exe`

## Estructura de Distribución

Después del build, la carpeta `dist/` contendrá:

```
dist/
├── dashboard.exe          # Aplicación principal
├── agente.exe            # Agente Python empaquetado
└── config.yaml           # Configuración del agente
```

## Ejecutar

```bash
# Desde la carpeta dist/
./dashboard.exe
```

El dashboard automáticamente encontrará y ejecutará `agente.exe` cuando se procesen archivos.

## Cómo Funciona la Integración

1. El usuario carga un PDF en el dashboard (interfaz Go)
2. El archivo se guarda temporalmente en `%TEMP%/tpia-dashboard/`
3. El dashboard invoca `agente.exe` con la ruta del archivo
4. El agente procesa el PDF y retorna el resultado
5. El resultado se muestra en el dashboard

## Descubrimiento Automático del Agente

El dashboard busca el agente en este orden:

1. **Ejecutable en mismo directorio**: `./agente.exe` o `./agente`
2. **Ejecutable en directorio padre**: `../agente.exe` o `../agente`
3. **Variable de entorno**: `$env:TPIA_AGENT_PATH`
4. **Código fuente (desarrollo)**: `../../agente/main.py` (requiere Python)

## Troubleshooting

### "Python is not installed or not in PATH"
```bash
# Verifica que Python esté en PATH
python --version

# Si no funciona, agrega Python al PATH:
# En Windows, edita las variables de entorno del sistema y agrega:
# C:\Users\{usuario}\AppData\Local\Programs\Python\Python311
```

### "Go is not installed or not in PATH"
```bash
# Verifica que Go esté instalado
go version

# Si no funciona, instala desde https://golang.org/dl/
```

### "wails: command not found"
```bash
# Instala Wails globalmente
go install github.com/wailsapp/wails/v2/cmd/wails@latest

# Verifica que GOBIN está en PATH
go env GOBIN
```

### Error: "No se pudo encontrar el directorio del agente"
- Asegúrate de que `agente.exe` está en el mismo directorio que `dashboard.exe`
- O establece la variable de entorno: `$env:TPIA_AGENT_PATH = "C:\ruta\a\agente.exe"`

### El agente no procesa archivos
- Verifica que `config.yaml` está en el mismo directorio que `agente.exe`
- Verifica que la variable de entorno `OPENAI_API_KEY` está configurada:
  ```bash
  $env:OPENAI_API_KEY = "tu-api-key-aqui"
  ```

## Desarrollo

Para desarrollar sin empaquetar:

### Agente (desarrollo)
```bash
cd p:\tpia\agente
python main.py -f "ruta/al/archivo.pdf"
```

### Dashboard (desarrollo)
```bash
cd p:\tpia\dashboard
wails dev
```

## Variables de Entorno

### Requeridas
- `OPENAI_API_KEY` - Tu API key de OpenAI

### Opcionales
- `TPIA_AGENT_PATH` - Ruta explícita al ejecutable del agente
- `TPIA_DEBUG` - Establecer a `1` para debug mode

## Notas sobre PyInstaller

El build de PyInstaller:
- Crea un ejecutable de una sola línea: `agente.exe`
- Incluye todas las dependencias Python
- El tamaño es aproximadamente 200-300MB (depende de las dependencias)
- Se ejecuta sin necesidad de Python instalado en la máquina de destino

Para reducir el tamaño:
```bash
pyinstaller --onefile --strip main.py  # Agrega --strip en Linux/macOS
```

## Reproducibilidad

Para builds reproducibles:
1. Usa versiones específicas de Python
2. Congela las dependencias: `pip freeze > requirements.lock.txt`
3. Usa Docker para builds multiplataforma

## Build Multiplataforma

Para compilar para múltiples plataformas:

```bash
# Windows
$env:GOOS="windows"; $env:GOARCH="amd64"; go build -o dashboard-windows.exe

# macOS
$env:GOOS="darwin"; $env:GOARCH="amd64"; go build -o dashboard-macos

# Linux
$env:GOOS="linux"; $env:GOARCH="amd64"; go build -o dashboard-linux
```

Para el agente Python (requiere PyInstaller cross-compilation):
```bash
# En la plataforma destino, ejecuta pyinstaller
```
