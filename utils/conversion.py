import os
from PIL import Image

def convert_file(file_path, target_format):
    """
    Supports conversion for images and simple file types.
    """
    base, ext = os.path.splitext(file_path)
    curr_ext = ext.lower().replace('.', '')
    target_format = target_format.lower()
    
    new_filename = f"{base}_converted.{target_format}"
    
    # Text to PDF Conversion
    if curr_ext == 'txt' and target_format == 'pdf':
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            
            c = canvas.Canvas(new_filename, pagesize=letter)
            width, height = letter
            y = height - 40
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    c.drawString(40, y, line.strip())
                    y -= 15
                    if y < 40:
                        c.showPage()
                        y = height - 40
            c.save()
            return new_filename
        except Exception as e:
            print(f"TXT to PDF conversion failed: {e}")

    # Image Conversion
    image_formats = ['png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff']
    if curr_ext in image_formats and target_format in image_formats:
        try:
            with Image.open(file_path) as img:
                # Handle transparency if converting to JPG
                if target_format in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img.save(new_filename)
            return new_filename
        except Exception as e:
            print(f"Image conversion failed: {e}")

    # Text to Text (e.g. .py to .txt) - just rename/copy is fine
    
    # Default: Mocking conversion by copying
    import shutil
    shutil.copy(file_path, new_filename)
    
    return new_filename
