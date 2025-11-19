import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text(path):
    """
    Extract text from image using Tesseract OCR.
    """
    try:
        # Open image
        image = Image.open(path)
        
        # Extract text
        text = pytesseract.image_to_string(image, lang='eng')
        
        return text.strip()
    
    except FileNotFoundError:
        return "Error: Image file not found."
    except Exception as e:
        return f"Error extracting text: {str(e)}"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        result = extract_text(sys.argv[1])
        print(result)
    else:
        print("Usage: python ocr_extract.py <image_path>")