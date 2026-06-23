#!/bin/bash

PYTHON_BIN=${1:-python}

echo "Instalando dependencias con $PYTHON_BIN usando requirements.txt..."

$PYTHON_BIN -m pip install -r requirements.txt

echo "Instalacion completada."
