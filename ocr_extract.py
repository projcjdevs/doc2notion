import pytesseract
from PIL import Image
import PyPDF2
from docx import Document
import os

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text(path):
    """
    Extract text from image, PDF, or DOCX files.
    Supports: .png, .jpg, .jpeg, .pdf, .docx
    """
    # Get the file extension (the part after the dot)
    file_ext = os.path.splitext(path)[1].lower()
    
    try:
        # IMAGE FILES (PNG, JPG, etc.)
        if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']:
            return extract_from_image(path)
        
        # PDF FILES
        elif file_ext == '.pdf':
            return extract_from_pdf(path)
        
        # WORD DOCUMENTS
        elif file_ext == '.docx':
            return extract_from_docx(path)
        
        # UNSUPPORTED FILE TYPE
        else:
            return f"Error: Unsupported file type '{file_ext}'. Supported: .png, .jpg, .pdf, .docx"
    
    except FileNotFoundError:
        return "Error: File not found. Check the file path."
    except Exception as e:
        return f"Error extracting text: {str(e)}"


def extract_from_image(path):
    """
    Extract text from image files using Tesseract OCR.
    """
    print(f"  📷 Processing image with OCR...")
    image = Image.open(path)
    text = pytesseract.image_to_string(image, lang='eng')
    return text.strip()


def extract_from_pdf(path):
    """
    Extract text from PDF files.
    """
    print(f"  📕 Processing PDF...")
    text = ""
    
    with open(path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        total_pages = len(pdf_reader.pages)
        print(f"  📄 Found {total_pages} pages")
        
        # Loop through each page
        for page_num in range(total_pages):
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            text += page_text + "\n\n"
            print(f"    ✓ Page {page_num + 1}/{total_pages}")
    
    return text.strip()


def extract_from_docx(path):
    """
    Extract text from Word documents (.docx).
    """
    print(f"  📘 Processing Word document...")
    doc = Document(path)
    
    # Extract text from all paragraphs
    paragraphs = []
    for para in doc.paragraphs:
        if para.text.strip():  # Only add non-empty paragraphs
            paragraphs.append(para.text)
    
    print(f"  📝 Found {len(paragraphs)} paragraphs")
    
    # Join all paragraphs with double line breaks
    text = "\n\n".join(paragraphs)
    return text.strip()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(f"\n🔍 Extracting text from: {file_path}\n")
        result = extract_text(file_path)
        print(f"\n📄 Extracted Text:\n{'-'*50}\n{result}\n{'-'*50}")
    else:
        print("Usage: python ocr_extract.py <file_path>")
        print("\nSupported formats:")
        print("  • Images: .png, .jpg, .jpeg, .bmp, .tiff")
        print("  • PDF: .pdf")
        print("  • Word: .docx")