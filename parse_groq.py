import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def parse_to_json(text: str) -> dict:
    """
    Extracts title and creates a detailed, structured summary from the document text.
    Returns a dict with 'title' and 'description'.
    """
    # Handle empty or garbage text
    if not text or len(text.strip()) < 10:
        return {
            "title": "Empty Document",
            "description": "No readable text was extracted from the document."
        }
    
    prompt = f"""You are an expert document analyzer and summarization specialist.

Your task: Analyze the document below and create a comprehensive, well-structured summary.

REQUIREMENTS:
1. **Title**: Generate a clear, descriptive title (5-10 words) that captures the document's main topic

2. **Summary**: Create a detailed summary (300-500 words) that includes:
   
   📌 **Overview**: 
   - What is this document about? (2-3 sentences)
   - Main purpose or objective
   
   🔑 **Key Points**:
   - List all important information using bullet points
   - Include specific details, numbers, dates, and facts
   - Organize by themes or sections if applicable
   
   📊 **Important Details**:
   - Highlight critical data, statistics, or findings
   - Mention any deadlines, amounts, or measurements
   - Note any action items or recommendations
   
   ✨ **Conclusion**:
   - Summarize the main takeaway
   - Mention any next steps or follow-up items

FORMATTING RULES:
- Use **bold** for section headers
- Use bullet points (•) for lists
- Use clear paragraph breaks for readability
- Keep the tone professional and concise
- Focus on substance over fluff

Return ONLY valid JSON in this exact format:
{{
  "title": "Your generated title here",
  "description": "**Overview**\\n\\nYour detailed summary here with proper formatting...\\n\\n**Key Points**\\n• Point 1\\n• Point 2\\n\\n**Important Details**\\n• Detail 1\\n• Detail 2\\n\\n**Conclusion**\\n\\nYour conclusion here."
}}

DOCUMENT TO ANALYZE:
---
{text}
---

JSON Response:"""

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,  # Slightly higher for better creativity
        max_tokens=2000   # Increased token limit for longer summaries
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