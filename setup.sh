#!/bin/bash

# TPIA Setup Script
# This script creates and configures the virtual environment for TPIA
# Uses --system-site-packages to reuse dependencies installed in the system Python

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
VENV_DIR="$SCRIPT_DIR/venv"
AGENTE_DIR="$SCRIPT_DIR/agente"

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

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    write_fail "Python 3 is not installed or not in PATH"
    exit 1
fi

write_success "======================================"
write_success "TPIA Setup Script"
write_success "======================================"
echo ""

PYTHON_VERSION=$(python3 --version 2>&1)
write_info "Using: $PYTHON_VERSION"
echo ""

# Create virtual environment with system site-packages
if [[ ! -d "$VENV_DIR" ]]; then
    write_info "Creating virtual environment with --system-site-packages..."
    python3 -m venv "$VENV_DIR" --system-site-packages
    write_success "[OK] Virtual environment created at $VENV_DIR"
else
    write_info "Virtual environment already exists at $VENV_DIR"
fi

echo ""
write_info "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
write_success "[OK] Virtual environment activated"

echo ""
write_info "Upgrading pip, setuptools, and wheel..."
"$VENV_DIR/bin/python3" -m pip install --upgrade pip setuptools wheel --quiet
write_success "[OK] pip, setuptools, and wheel upgraded"

echo ""
write_info "Installing PyInstaller (required for agent compilation)..."
"$VENV_DIR/bin/python3" -m pip install pyinstaller --quiet
write_success "[OK] PyInstaller installed"

echo ""
write_info "Verifying agent dependencies are available..."

# Check for key dependencies
DEPS_OK=true
MISSING_DEPS=""

for pkg in pymupdf pytesseract Pillow groq pyyaml python-dotenv langgraph langchain chromadb sentence-transformers; do
    if ! "$VENV_DIR/bin/python3" -c "import $(echo $pkg | sed 's/-/_/g')" 2>/dev/null; then
        MISSING_DEPS="$MISSING_DEPS $pkg"
        DEPS_OK=false
    fi
done

if [[ "$DEPS_OK" == true ]]; then
    write_success "[OK] All agent dependencies are available (from system Python)"
else
    write_info "Some dependencies not found in system Python. Installing missing packages..."
    write_info "Missing: $MISSING_DEPS"
    
    # Only install missing ones from requirements.txt
    if [[ -f "$AGENTE_DIR/requirements.txt" ]]; then
        "$VENV_DIR/bin/python3" -m pip install -r "$AGENTE_DIR/requirements.txt" --quiet 2>/dev/null || true
        write_success "[OK] Attempted to install missing dependencies"
    fi
fi

echo ""
write_success "======================================"
write_success "Setup completed successfully!"
write_success "======================================"
echo ""
write_info "To activate the virtual environment, run:"
write_info "  source venv/bin/activate"
echo ""
write_info "To run the build script, use:"
write_info "  ./build.sh"
echo ""
write_info "The build.sh script will automatically use the virtual environment."
write_info "System Python packages are accessible from the venv (--system-site-packages)."
