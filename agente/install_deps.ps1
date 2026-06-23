param (
    [string]$PythonBin = "python"
)

Write-Host "Instalando dependencias con $PythonBin usando requirements.txt..."

& $PythonBin -m pip install -r requirements.txt

Write-Host "Instalacion completada."
