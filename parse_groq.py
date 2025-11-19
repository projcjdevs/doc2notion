import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def parse_to_json(text: str) -> dict:
    """
    Extracts title and creates a summary from the document text.
    Returns a dict with 'title' and 'description'.
    """
    # Handle empty or garbage text
    if not text or len(text.strip()) < 10:
        return {
            "title": "Empty Document",
            "description": "No readable text was extracted from the document."
        }
    
    prompt = f"""
You are an expert document analyzer.

From the following document, extract:
1. A concise title (max 10 words)
2. A clear, structured summary

Return ONLY valid JSON in this format:
{{
  "title": "The document title here",
  "description": "A comprehensive summary of the document content."
}}

Document:
{text}
"""

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    response = completion.choices[0].message.content.strip()
    
    # Remove markdown code blocks if present
    if response.startswith("```"):
        lines = response.split("\n")
        response = "\n".join(lines[1:-1])
        if response.startswith("json"):
            response = response[4:].strip()
    
    # Parse the JSON response
    try:
        data = json.loads(response)
        # Ensure title is not empty
        if not data.get("title") or not data.get("title").strip():
            data["title"] = "Untitled Document"
        return data
    except json.JSONDecodeError:
        # Fallback if LLM doesn't return valid JSON
        return {
            "title": "Document Summary",
            "description": response
        }