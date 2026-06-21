@echo off
set PYTHON_BIN=%1
if "%~1"=="" set PYTHON_BIN=python

echo Instalando dependencias con %PYTHON_BIN%...

%PYTHON_BIN% -m pip install PyPDF2==3.0.1
%PYTHON_BIN% -m pip install pyyaml==6.0.1
%PYTHON_BIN% -m pip install python-dotenv==1.0.1
%PYTHON_BIN% -m pip install openai==1.14.0
%PYTHON_BIN% -m pip install tabulate==0.9.0
%PYTHON_BIN% -m pip install langgraph
%PYTHON_BIN% -m pip install langchain-groq
%PYTHON_BIN% -m pip install langchain-core
%PYTHON_BIN% -m pip install chromadb
%PYTHON_BIN% -m pip install langchain-chroma
%PYTHON_BIN% -m pip install langchain-huggingface
%PYTHON_BIN% -m pip install langchain-community
%PYTHON_BIN% -m pip install langchain-classic
%PYTHON_BIN% -m pip install rank_bm25
%PYTHON_BIN% -m pip install sentence-transformers

echo Instalacion completada.
