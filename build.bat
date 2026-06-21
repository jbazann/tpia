@echo off
REM TPIA Build Script Launcher
REM This batch file makes it easier to run the PowerShell build script

setlocal enabledelayedexpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"

REM Default parameters
set "BUILD_TYPE=release"
set "SKIP_AGENT="
set "SKIP_DASHBOARD="

REM Parse command line arguments
:parse_args
if "%~1"=="" goto run_build
if /i "%~1"=="debug" (
    set "BUILD_TYPE=debug"
    shift
    goto parse_args
)
if /i "%~1"=="release" (
    set "BUILD_TYPE=release"
    shift
    goto parse_args
)
if /i "%~1"=="--skip-agent" (
    set "SKIP_AGENT=-SkipAgentBuild"
    shift
    goto parse_args
)
if /i "%~1"=="--skip-dashboard" (
    set "SKIP_DASHBOARD=-SkipDashboardBuild"
    shift
    goto parse_args
)
if /i "%~1"=="--help" (
    echo TPIA Build Script
    echo.
    echo Usage: build.bat [OPTIONS]
    echo.
    echo Options:
    echo   debug                   Build in debug mode
    echo   release                 Build in release mode (default)
    echo   --skip-agent           Skip building the agent
    echo   --skip-dashboard       Skip building the dashboard
    echo   --help                 Show this help message
    echo.
    exit /b 0
)
shift
goto parse_args

:run_build
echo Launching TPIA Build Script...
echo.

REM Run the PowerShell script
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%build.ps1" -BuildType "%BUILD_TYPE%" %SKIP_AGENT% %SKIP_DASHBOARD%

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

pause
exit /b 0
