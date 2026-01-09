import io
import os
from pypdf import PdfReader
from docx import Document

def extract_text_content(data, filename):
    """
    Attempts to extract readable text from various file formats.
    Returns (text, is_extracted)
    """
    ext = os.path.splitext(filename)[1].lower()
    
    try:
        if ext == '.pdf':
            reader = PdfReader(io.BytesIO(data))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip(), True
            
        elif ext == '.docx':
            doc = Document(io.BytesIO(data))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text.strip(), True
            
        elif ext in ['.txt', '.py', '.js', '.css', '.html', '.md', '.json', '.csv']:
            try:
                return data.decode('utf-8'), False
            except UnicodeDecodeError:
                return data.decode('latin-1'), False
                
    except Exception as e:
        print(f"Extraction failed for {filename}: {e}")
        
    # Fallback to general text decoding if extraction fails or format is unknown
    try:
        return data.decode('utf-8'), False
    except UnicodeDecodeError:
        return data.decode('latin-1'), False
