# TPIA Build Script
# This script packages the Python agent with PyInstaller and builds the Go dashboard with Wails

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("debug", "release")]
    [string]$BuildType = "release",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipAgentBuild = $false,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipDashboardBuild = $false
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AgenteDir = Join-Path $ScriptDir "agente"
$DashboardDir = Join-Path $ScriptDir "dashboard"
$OutputDir = Join-Path $ScriptDir "dist"

# Colors for output
$Green = [System.ConsoleColor]::Green
$Yellow = [System.ConsoleColor]::Yellow
$Red = [System.ConsoleColor]::Red

function Write-Success {
    param([string]$Message)
    Write-Host $Message -ForegroundColor $Green
}

function Write-Info {
    param([string]$Message)
    Write-Host $Message -ForegroundColor $Yellow
}

function Write-Fail {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor $Red
}

# Verify Python is installed
function Test-PythonInstalled {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Write-Fail "Python is not installed or not in PATH"
        return $false
    }
    try {
        $version = & python --version 2>&1
        Write-Success "[OK] Python found: $version"
        return $true
    } catch {
        Write-Fail "Python is not usable: $_"
        return $false
    }
}

# Verify Go is installed
function Test-GoInstalled {
    $cmd = Get-Command go -ErrorAction SilentlyContinue
    if (-not $cmd) {
        Write-Fail "Go is not installed or not in PATH"
        return $false
    }
    try {
        $version = & go version 2>&1
        Write-Success "[OK] Go found: $version"
        return $true
    } catch {
        Write-Fail "Go is not usable: $_"
        return $false
    }
}

# Install PyInstaller
function Install-PyInstaller {
    Write-Info "Installing PyInstaller..."
    python -m pip install pyinstaller --quiet
    Write-Success "[OK] PyInstaller installed"
}

# Build the Python agent
function Build-Agent {
    if ($SkipAgentBuild) {
        Write-Info "[-] Skipping agent build (--SkipAgentBuild flag set)"
        return $true
    }

    Write-Info "Building Python agent..."
    
    # Check if PyInstaller is installed
    try {
        python -m PyInstaller --version | Out-Null
    } catch {
        Install-PyInstaller
    }

    # Install agent dependencies
    Write-Info "Installing agent dependencies..."
    Set-Location $AgenteDir
    python -m pip install -r requirements.txt --quiet
    Set-Location $ScriptDir

    # Copy config.yaml to a location where PyInstaller can bundle it
    Write-Info "Preparing agent resources..."
    $distAgentDir = Join-Path $AgenteDir "dist"
    
    # Build with PyInstaller
    Write-Info "Running PyInstaller..."
    $specFile = Join-Path $AgenteDir "agente.spec"
    
    # Prefer a direct pyinstaller onefile invocation for simplicity
    Write-Info "Creating PyInstaller bundle (onefile)..."
    Set-Location $AgenteDir

    # Install requirements (quiet) -- continue if this fails but warn
    try {
        python -m pip install -r requirements.txt --quiet
    } catch {
        Write-Info "Warning: failed installing some agent dependencies: $_"
    }

    # Add-data delimiter differs by platform
    if ($env:OS -eq 'Windows_NT') {
        $addData = 'config.yaml;.'
    } else {
        $addData = 'config.yaml:.'
    }

    # Run PyInstaller
    try {
        python -m PyInstaller --onefile --name "agente" --add-data "$addData" --distpath dist --workpath build --clean main.py --noconfirm
    } catch {
        Write-Fail "PyInstaller failed: $_"
        Set-Location $ScriptDir
        return $false
    }

    Set-Location $ScriptDir

    # Expected output location
    $expected = Join-Path (Join-Path $AgenteDir 'dist') 'agente.exe'

    if (Test-Path $expected) {
        Write-Success "[OK] Agent built successfully: $expected"
        return $true
    } else {
        Write-Fail "Agent build failed - expected executable not found at $expected"
        return $false
    }
}

# Build the Go dashboard
function Build-Dashboard {
    if ($SkipDashboardBuild) {
        Write-Info "[-] Skipping dashboard build (--SkipDashboardBuild flag set)"
        return $true
    }

    Write-Info "Building Go dashboard..."

    Set-Location $DashboardDir
    
    # Install frontend dependencies
    Write-Info "Installing frontend dependencies..."
    Set-Location (Join-Path $DashboardDir "frontend")
    npm install --silent
    Set-Location $DashboardDir

    # Build with Wails
    Write-Info "Running Wails build..."
    if ($BuildType -eq "debug") {
        wails build -debug -webpackdir "./frontend" -o dashboard-debug 2>&1
    } else {
        wails build -webpackdir "./frontend" -o dashboard 2>&1
    }

    Set-Location $ScriptDir

    # Check if build was successful
    $exeName = if ($BuildType -eq "debug") { "dashboard-debug.exe" } else { "dashboard.exe" }
    $dashboardExe = Join-Path $DashboardDir "build/bin" $exeName

    if (Test-Path $dashboardExe) {
        Write-Success "[OK] Dashboard built successfully: $dashboardExe"
        return $true
    } else {
        Write-Fail "Dashboard build failed - executable not found at $dashboardExe"
        return $false
    }
}

# Copy agent executable to dashboard
function Copy-AgentToDashboard {
    Write-Info "Copying agent executable to dashboard..."

    # Strictly require agente/dist/agente.exe
    $agentExe = Join-Path (Join-Path $AgenteDir 'dist') 'agente.exe'
    $dashboardDir = Join-Path $ScriptDir "dashboard"

    if (Test-Path $agentExe) {
        # Create resources directory if needed
        $resourcesDir = Join-Path $dashboardDir "resources"
        if (-not (Test-Path $resourcesDir)) {
            New-Item -ItemType Directory -Path $resourcesDir -Force | Out-Null
        }

        Copy-Item -Path $agentExe -Destination (Join-Path $resourcesDir "agente.exe") -Force
        Write-Success "[OK] Agent executable copied to dashboard"
        return $true
    } else {
        Write-Fail "Agent executable not found at $agentExe"
        return $false
    }
}

# Create distribution folder with both executables
function Create-Distribution {
    Write-Info "Creating distribution folder..."

    # Create output directory
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }

    # Copy dashboard executable
    $exeName = if ($BuildType -eq "debug") { "dashboard-debug.exe" } else { "dashboard.exe" }
    $dashboardExe = Join-Path $DashboardDir "build/bin" $exeName
    $dashboardOutput = Join-Path $OutputDir $exeName

    if (Test-Path $dashboardExe) {
        Copy-Item -Path $dashboardExe -Destination $dashboardOutput -Force
        Write-Success "[OK] Dashboard executable copied to dist/"
    } else {
        if ($SkipDashboardBuild) {
            Write-Info "[-] Dashboard build skipped, no dashboard binary copied to dist/"
        } else {
            Write-Fail "Dashboard executable not found at $dashboardExe - cannot include in distribution"
        }
    }

    # Strictly require agente/dist/agente.exe
    $agentExe = Join-Path (Join-Path $AgenteDir 'dist') 'agente.exe'
    if (Test-Path $agentExe) {
        $agentOutput = Join-Path $OutputDir "agente.exe"
        Copy-Item -Path $agentExe -Destination $agentOutput -Force
        Write-Success "[OK] Agent executable copied to dist/"
    } else {
        if ($SkipAgentBuild) {
            Write-Info "[-] Agent build skipped, no agent binary copied to dist/"
        } else {
            Write-Fail "Agent executable not found at $agentExe - cannot include in distribution"
        }
    }

    # Copy config.yaml
    $configFile = Join-Path $AgenteDir "config.yaml"
    if (Test-Path $configFile) {
        Copy-Item -Path $configFile -Destination (Join-Path $OutputDir "config.yaml") -Force
        Write-Success "[OK] Config file copied to dist/"
    }
    
    Write-Success "[OK] Distribution folder created: $OutputDir"
}

# Main build flow
function Main {
    Write-Info "======================================"
    Write-Info "TPIA Build Script"
    Write-Info "Build Type: $BuildType"
    Write-Info "======================================"
    Write-Host ""

    # Pre-build checks
    if (-not (Test-PythonInstalled)) {
        exit 1
    }

    if (-not (Test-GoInstalled)) {
        exit 1
    }

    # Build agent
    if (-not $SkipAgentBuild) {
        if (-not (Build-Agent)) {
            exit 1
        }
    }

    # Build dashboard
    if (-not $SkipDashboardBuild) {
        if (-not (Build-Dashboard)) {
            exit 1
        }

        # Copy agent to dashboard after dashboard build
        if (-not $SkipAgentBuild) {
            if (-not (Copy-AgentToDashboard)) {
                Write-Info "Warning: Agent executable not copied to dashboard"
            }
        }
    }

    # Create distribution
    Create-Distribution

    Write-Host ""
    Write-Success "======================================"
    Write-Success "Build completed successfully!"
    Write-Success "======================================"
    
    if (Test-Path $OutputDir) {
        Write-Info "Output directory: $OutputDir"
        Write-Info "Run the dashboard:"
        Write-Info "  .\dist\dashboard.exe"
    }
}

# Run main
Main
