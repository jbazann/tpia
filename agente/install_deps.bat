@echo off
set PYTHON_BIN=%1
if "%~1"=="" set PYTHON_BIN=python

echo Instalando dependencias con %PYTHON_BIN% usando requirements.txt...

%PYTHON_BIN% -m pip install -r requirements.txt

echo Instalacion completada.
