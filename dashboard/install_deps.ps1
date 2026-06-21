Write-Host "Verificando dependencias preinstaladas del sistema..." -ForegroundColor Cyan

# Verificar Go
if (-not (Get-Command "go" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Go no está instalado o no se encuentra en el PATH." -ForegroundColor Red
    Write-Host "Por favor instale Go (https://golang.org/doc/install) y vuelva a intentarlo." -ForegroundColor Yellow
    exit 1
}

# Verificar npm (Node.js)
if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js (npm) no está instalado o no se encuentra en el PATH." -ForegroundColor Red
    Write-Host "Por favor instale Node.js (https://nodejs.org/) y vuelva a intentarlo." -ForegroundColor Yellow
    exit 1
}

Write-Host "Todas las herramientas base encontradas. Iniciando instalacion..." -ForegroundColor Green

Write-Host "`n[1/3] Instalando Wails CLI..." -ForegroundColor Cyan
go install github.com/wailsapp/wails/v2/cmd/wails@latest
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error instalando Wails CLI." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n[2/3] Descargando dependencias de Go (Backend)..." -ForegroundColor Cyan
go mod download
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error descargando dependencias de Go." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n[3/3] Instalando dependencias de Node.js (Frontend)..." -ForegroundColor Cyan
if (Test-Path "frontend/package.json") {
    Push-Location frontend
    npm install
    $npmExit = $LASTEXITCODE
    Pop-Location
    if ($npmExit -ne 0) {
        Write-Host "Error instalando dependencias de npm." -ForegroundColor Red
        exit $npmExit
    }
} else {
    Write-Host "ADVERTENCIA: No se encontro package.json en el directorio frontend." -ForegroundColor Yellow
}

Write-Host "`nInstalacion de dependencias completada con exito." -ForegroundColor Green
