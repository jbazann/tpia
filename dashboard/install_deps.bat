@echo off
echo ========================================================
echo Instalador de Dependencias del Dashboard (TPIA)
echo ========================================================
echo.

REM Delegar la ejecucion al script de PowerShell
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0install_deps.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo ========================================================
    echo Error durante la instalacion de dependencias.
    echo ========================================================
    exit /b %ERRORLEVEL%
)

echo.
pause
