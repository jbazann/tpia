param (
    [string]$PythonBin = "python"
)

Write-Host "Instalando dependencias con $PythonBin..."

$deps = @(
    "PyPDF2==3.0.1",
    "pyyaml==6.0.1",
    "python-dotenv==1.0.1",
    "openai==1.14.0",
    "tabulate==0.9.0",
    "langgraph",
    "langchain-groq",
    "langchain-core",
    "chromadb",
    "langchain-chroma",
    "langchain-huggingface",
    "langchain-community",
    "langchain-classic",
    "rank_bm25",
    "sentence-transformers"
)

foreach ($dep in $deps) {
    & $PythonBin -m pip install $dep
}

Write-Host "Instalacion completada."
