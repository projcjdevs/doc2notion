from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from ocr_extract import extract_text
from parse_groq import parse_to_json
from push2notion import push

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.docx', '.doc'}

def is_allowed_file(filename: str, content_type: str) -> bool:
    """
    Check if file is allowed based on extension and content type.
    More flexible validation that handles different MIME types.
    """
    # Get file extension
    _, ext = os.path.splitext(filename.lower())
    
    # Check extension
    if ext not in ALLOWED_EXTENSIONS:
        return False
    
    # Accept if content type is in allowed list (flexible matching)
    allowed_content_types = [
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/heic', 
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  
        'application/msword', 
        'application/octet-stream',  
    ]
    
    # If content type matches OR it's a generic type with valid extension
    if content_type in allowed_content_types or content_type == 'application/octet-stream':
        return True
    
    # Also accept if content_type contains any of our keywords
    content_lower = content_type.lower()
    if any(keyword in content_lower for keyword in ['image', 'pdf', 'word', 'document']):
        return True
    
    return False

@app.get("/")
def read_root():
    return {"status": "Doc2Notion API is running! 🚀"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Main endpoint: receives image/document from mobile app,
    processes it, and creates Notion page.
    """
    print(f"\n📱 Received file: {file.filename}")
    print(f"📋 Content type: {file.content_type}")
    
    # Validate file
    if not is_allowed_file(file.filename, file.content_type):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.filename} ({file.content_type}). Allowed: JPG, PNG, PDF, DOCX"
        )
    
    try:
        # Determine file extension
        _, ext = os.path.splitext(file.filename.lower())
        if not ext:
            # Fallback based on content type
            if 'image' in file.content_type:
                ext = '.jpg'
            elif 'pdf' in file.content_type:
                ext = '.pdf'
            elif 'word' in file.content_type or 'document' in file.content_type:
                ext = '.docx'
            else:
                ext = '.tmp'
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        print(f"Saved to: {tmp_path}")
        print(f"File size: {len(content) / 1024:.1f} KB")
        
        # Extract text
        print("Extracting text via OCR...")
        text = extract_text(tmp_path)
        
        if not text or len(text.strip()) < 10:
            raise HTTPException(
                status_code=422,
                detail="Could not extract readable text from the document. Please ensure the document contains text or clear images."
            )
        
        print(f"📄 Extracted {len(text)} characters")
        
        # Summarize with AI
        print("Parsing with Groq AI...")
        data = parse_to_json(text)
        print(f"Title: {data.get('title')}")
        
        # Push to Notion
        print("Pushing to Notion...")
        page_id = push(data, tmp_path)
        
        # Clean up
        os.unlink(tmp_path)
        print(f"Success! Page ID: {page_id}\n")
        
        return {
            "success": True,
            "page_id": page_id,
            "title": data.get("title"),
            "description_preview": data.get("description", "")[:100] + "...",
            "message": "Document successfully uploaded to Notion!"
        }
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Clean up temp file if it exists
        if 'tmp_path' in locals():
            try:
                os.unlink(tmp_path)
            except:
                pass
        
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Processing error: {str(e)}"
        )

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "doc2notion"}

if __name__ == "__main__":
    import uvicorn
    print("\nStarting Doc2Notion API Server...")
    print("Server will run on: http://0.0.0.0:8000")
    print("Access from phone using your computer's IP address")
    print("Supported formats: JPG, PNG, PDF, DOCX\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)