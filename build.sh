#!/bin/bash

# TPIA Build Script
# This script packages the Python agent with PyInstaller and builds the Go dashboard with Wails

# Default values
BUILD_TYPE="release"
SKIP_AGENT_BUILD=false
SKIP_DASHBOARD_BUILD=false

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AGENTE_DIR="$SCRIPT_DIR/agente"
DASHBOARD_DIR="$SCRIPT_DIR/dashboard"
OUTPUT_DIR="$SCRIPT_DIR/dist"
VENV_DIR="$SCRIPT_DIR/venv"

# Python interpreter
PYTHON="$VENV_DIR/bin/python3"

# Function to print colored output
write_success() {
    echo -e "${GREEN}$1${NC}"
}

write_info() {
    echo -e "${YELLOW}$1${NC}"
}

write_fail() {
    echo -e "${RED}ERROR: $1${NC}"
}

# Print usage information
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE              Build type: debug or release (default: release)"
    echo "  -s, --skip-agent             Skip agent build"
    echo "  -d, --skip-dashboard         Skip dashboard build"
    echo "  -h, --help                   Show this help message"
    echo ""
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BUILD_TYPE="$2"
            if [[ "$BUILD_TYPE" != "debug" && "$BUILD_TYPE" != "release" ]]; then
                write_fail "Invalid build type: $BUILD_TYPE (must be 'debug' or 'release')"
                exit 1
            fi
            shift 2
            ;;
        -s|--skip-agent)
            SKIP_AGENT_BUILD=true
            shift
            ;;
        -d|--skip-dashboard)
            SKIP_DASHBOARD_BUILD=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            write_fail "Unknown option: $1"
            usage
            ;;
    esac
done

set -e

# Verify Python is installed and setup virtual environment
test_python_installed() {
    if ! command -v python3 &> /dev/null; then
        write_fail "Python is not installed or not in PATH"
        return 1
    fi
    
    local version
    version=$(python3 --version 2>&1)
    write_success "[OK] Python found: $version"
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "$VENV_DIR" ]]; then
        write_info "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        write_success "[OK] Virtual environment created"
    fi
    
    # Verify venv python exists
    if [[ ! -f "$PYTHON" ]]; then
        write_fail "Virtual environment Python not found at $PYTHON"
        return 1
    fi
    
    return 0
}

# Verify Go is installed
test_go_installed() {
    if ! command -v go &> /dev/null; then
        write_fail "Go is not installed or not in PATH"
        return 1
    fi
    
    local version
    version=$(go version 2>&1)
    write_success "[OK] Go found: $version"
    return 0
}

# Install PyInstaller
install_pyinstaller() {
    write_info "Installing PyInstaller..."
    "$PYTHON" -m pip install pyinstaller --quiet
    write_success "[OK] PyInstaller installed"
}

# Build the Python agent
build_agent() {
    if [[ "$SKIP_AGENT_BUILD" == true ]]; then
        write_info "[-] Skipping agent build (--skip-agent flag set)"
        return 0
    fi

    write_info "Building Python agent..."
    
    # Check if PyInstaller is installed
    if ! "$PYTHON" -m PyInstaller --version &> /dev/null; then
        install_pyinstaller
    fi

    # Install agent dependencies
    write_info "Installing agent dependencies..."
    pushd "$AGENTE_DIR" > /dev/null
    
    # Install requirements (quiet) -- continue if this fails but warn
    if ! "$PYTHON" -m pip install -r requirements.txt --quiet 2>/dev/null; then
        write_info "Warning: failed installing some agent dependencies"
    fi

    # Run PyInstaller
    write_info "Creating PyInstaller bundle (onefile)..."
    if ! "$PYTHON" -m PyInstaller \
        --onefile \
        --name "agente" \
        --add-data "config.yaml:." \
        --distpath dist \
        --workpath build \
        --clean \
        main.py \
        --noconfirm > /dev/null 2>&1; then
        write_fail "PyInstaller failed"
        popd > /dev/null
        return 1
    fi

    popd > /dev/null

    # Expected output location
    local expected="$AGENTE_DIR/dist/agente"
    
    if [[ -f "$expected" ]]; then
        write_success "[OK] Agent built successfully: $expected"
        return 0
    else
        write_fail "Agent build failed - expected executable not found at $expected"
        return 1
    fi
}

# Build the Go dashboard
build_dashboard() {
    if [[ "$SKIP_DASHBOARD_BUILD" == true ]]; then
        write_info "[-] Skipping dashboard build (--skip-dashboard flag set)"
        return 0
    fi

    write_info "Building Go dashboard..."

    pushd "$DASHBOARD_DIR" > /dev/null
    
    # Install frontend dependencies
    write_info "Installing frontend dependencies..."
    pushd "frontend" > /dev/null
    npm install --silent
    popd > /dev/null

    # Build with Wails
    write_info "Running Wails build..."
    if [[ "$BUILD_TYPE" == "debug" ]]; then
        if ! wails build -debug -o dashboard-debug 2>&1; then
            write_fail "Wails build failed (debug mode)"
            popd > /dev/null
            return 1
        fi
    else
        if ! wails build -o dashboard 2>&1; then
            write_fail "Wails build failed (release mode)"
            popd > /dev/null
            return 1
        fi
    fi

    popd > /dev/null

    # Check if build was successful
    local exe_name
    if [[ "$BUILD_TYPE" == "debug" ]]; then
        exe_name="dashboard-debug"
    else
        exe_name="dashboard"
    fi
    
    local dashboard_exe="$DASHBOARD_DIR/build/bin/$exe_name"

    if [[ -f "$dashboard_exe" ]]; then
        write_success "[OK] Dashboard built successfully: $dashboard_exe"
        return 0
    else
        write_fail "Dashboard build failed - executable not found at $dashboard_exe"
        return 1
    fi
}

# Copy agent executable to dashboard
copy_agent_to_dashboard() {
    write_info "Copying agent executable to dashboard..."

    local agent_exe="$AGENTE_DIR/dist/agente"
    local resources_dir="$DASHBOARD_DIR/resources"

    if [[ -f "$agent_exe" ]]; then
        # Create resources directory if needed
        if [[ ! -d "$resources_dir" ]]; then
            mkdir -p "$resources_dir"
        fi

        cp "$agent_exe" "$resources_dir/agente"
        write_success "[OK] Agent executable copied to dashboard"
        return 0
    else
        write_fail "Agent executable not found at $agent_exe"
        return 1
    fi
}

# Create distribution folder with both executables
create_distribution() {
    write_info "Creating distribution folder..."

    # Create output directory
    if [[ ! -d "$OUTPUT_DIR" ]]; then
        mkdir -p "$OUTPUT_DIR"
    fi

    # Copy dashboard executable
    local exe_name
    if [[ "$BUILD_TYPE" == "debug" ]]; then
        exe_name="dashboard-debug"
    else
        exe_name="dashboard"
    fi
    
    local dashboard_exe="$DASHBOARD_DIR/build/bin/$exe_name"
    local dashboard_output="$OUTPUT_DIR/$exe_name"

    if [[ -f "$dashboard_exe" ]]; then
        cp "$dashboard_exe" "$dashboard_output"
        write_success "[OK] Dashboard executable copied to dist/"
    else
        if [[ "$SKIP_DASHBOARD_BUILD" == true ]]; then
            write_info "[-] Dashboard build skipped, no dashboard binary copied to dist/"
        else
            write_fail "Dashboard executable not found at $dashboard_exe - cannot include in distribution"
        fi
    fi

    # Copy agent executable
    local agent_exe="$AGENTE_DIR/dist/agente"
    if [[ -f "$agent_exe" ]]; then
        local agent_output="$OUTPUT_DIR/agente"
        cp "$agent_exe" "$agent_output"
        write_success "[OK] Agent executable copied to dist/"
    else
        if [[ "$SKIP_AGENT_BUILD" == true ]]; then
            write_info "[-] Agent build skipped, no agent binary copied to dist/"
        else
            write_fail "Agent executable not found at $agent_exe - cannot include in distribution"
        fi
    fi

    # Copy config.yaml
    local config_file="$AGENTE_DIR/config.yaml"
    if [[ -f "$config_file" ]]; then
        cp "$config_file" "$OUTPUT_DIR/config.yaml"
        write_success "[OK] Config file copied to dist/"
    fi
    
    write_success "[OK] Distribution folder created: $OUTPUT_DIR"
}

# Main build flow
main() {
    write_info "======================================"
    write_info "TPIA Build Script"
    write_info "Build Type: $BUILD_TYPE"
    write_info "======================================"
    echo ""

    # Pre-build checks
    if ! test_python_installed; then
        exit 1
    fi

    if ! test_go_installed; then
        exit 1
    fi

    # Build agent
    if [[ "$SKIP_AGENT_BUILD" != true ]]; then
        if ! build_agent; then
            exit 1
        fi
    fi

    # Build dashboard
    if [[ "$SKIP_DASHBOARD_BUILD" != true ]]; then
        if ! build_dashboard; then
            exit 1
        fi

        # Copy agent to dashboard after dashboard build
        if [[ "$SKIP_AGENT_BUILD" != true ]]; then
            if ! copy_agent_to_dashboard; then
                write_info "Warning: Agent executable not copied to dashboard"
            fi
        fi
    fi

    # Create distribution
    create_distribution

    echo ""
    write_success "======================================"
    write_success "Build completed successfully!"
    write_success "======================================"
    
    if [[ -d "$OUTPUT_DIR" ]]; then
        write_info "Output directory: $OUTPUT_DIR"
        write_info "Run the dashboard:"
        write_info "  ./dist/dashboard"
    fi
}

# Run main
main
