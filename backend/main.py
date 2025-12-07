from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from ocr_extract import extract_text
from parse_groq import parse_to_json
from push2notion import push

app = FastAPI()

# Allow mobile app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your mobile app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Doc2Notion API is running! 🚀"}

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Endpoint to upload an image, extract text, summarize, and push to Notion.
    """
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail="Only .jpg and .png files are supported"
        )
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        # Process the document
        print("🔍 Extracting text via OCR...")
        text = extract_text(tmp_path)
        
        print("🤖 Parsing with Groq...")
        data = parse_to_json(text)
        
        print("📤 Pushing to Notion...")
        page_id = push(data)
        
        # Clean up temp file
        os.unlink(tmp_path)
        
        return {
            "success": True,
            "page_id": page_id,
            "title": data.get("title"),
            "message": "Document successfully uploaded to Notion!"
        }
    
    except Exception as e:
        # Clean up temp file if it exists
        if 'tmp_path' in locals():
            os.unlink(tmp_path)
        
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)