import PyPDF2
import os

def read_pdf(file_path: str) -> str:
    """Extrae el texto de un archivo PDF."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo PDF '{file_path}' no existe.")
    
    if not file_path.lower().endswith('.pdf'):
        raise ValueError(f"El archivo '{file_path}' no es un PDF válido.")
    
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            if len(reader.pages) == 0:
                raise ValueError("El PDF no contiene páginas.")
            
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
                    
    except PyPDF2.PdfReadError as e:
        raise ValueError(f"Error al leer el PDF - posiblemente corrupto: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error inesperado al procesar el PDF: {str(e)}")
    
    if not text or text.strip() == "":
        raise ValueError("El PDF no contiene texto extraíble.")
    
    return text
