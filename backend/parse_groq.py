import os
import json
import re
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
    
    prompt = f"""You are a professional content analyst. Extract a clear title and create a detailed summary.

CRITICAL: Return ONLY valid JSON. No extra text before or after. No explanations.

The description field must contain ONLY the formatted summary text, NOT the JSON structure itself.

Format:
{{
  "title": "Clear, specific title (5-10 words describing the document)",
  "description": "**Overview**\\n[2-3 sentences about main topic]\\n\\n**Key Points**\\n• [Point 1]\\n• [Point 2]\\n• [Point 3]\\n\\n**Important Details**\\n• [Detail 1]\\n• [Detail 2]\\n\\n**Conclusion**\\n[Main takeaway]"
}}

DOCUMENT TEXT:
{text}

Return JSON now:"""

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",  
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, 
        max_tokens=2000
    )

    response = completion.choices[0].message.content.strip()
    
    print(f"🤖 Raw Groq response:\n{response}\n")
    
    # Remove markdown code blocks
    if "```" in response:
        # Extract content between ``` markers
        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            response = match.group(1)
    
    # Extract JSON object (most robust method)
    # Find the outermost { and }
    stack = []
    start = -1
    end = -1
    
    for i, char in enumerate(response):
        if char == '{':
            if not stack:
                start = i
            stack.append(char)
        elif char == '}':
            if stack:
                stack.pop()
                if not stack:
                    end = i
                    break
    
    if start != -1 and end != -1:
        json_str = response[start:end+1]
    else:
        json_str = response
    
    print(f"📦 Extracted JSON string:\n{json_str}\n")
    
    # Parse JSON
    try:
        data = json.loads(json_str)
        
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        
        # If description contains JSON-like patterns, extract only the actual text
        if description.startswith('{') or '"title"' in description[:100]:
            print("⚠️  Warning: JSON detected in description field, cleaning...")
            
            # Try to parse it as nested JSON
            try:
                nested = json.loads(description)
                description = nested.get("description", description)
            except:
                pass
            
            # Remove any remaining JSON artifacts
            # Find where the actual summary starts (after the JSON structure)
            lines = description.split('\n')
            clean_lines = []
            found_start = False
            
            for line in lines:
                # Skip lines with JSON structure
                if any(marker in line for marker in ['{', '}', '"title":', '"description":']):
                    continue
                # Start collecting after we pass JSON
                if '**Overview**' in line or '**Key Points**' in line:
                    found_start = True
                if found_start or (line.strip() and not line.strip().startswith('"')):
                    clean_lines.append(line)
            
            description = '\n'.join(clean_lines).strip()
        
        # Ensure we have valid data
        if not title:
            title = "Untitled Document"
        
        if not description or len(description) < 20:
            description = "Summary could not be generated. Please check the document text."
        
        print(f"✅ Final title: {title}")
        print(f"✅ Final description length: {len(description)} chars\n")
        
        return {
            "title": title,
            "description": description
        }
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing failed: {e}")
        print(f"📄 Tried to parse: {json_str[:200]}...")
        
        # Manual extraction fallback
        title_pattern = r'"title"\s*:\s*"([^"]+)"'
        desc_pattern = r'"description"\s*:\s*"((?:[^"\\]|\\.)+)"'
        
        title_match = re.search(title_pattern, response)
        desc_match = re.search(desc_pattern, response, re.DOTALL)
        
        title = title_match.group(1) if title_match else "Document Summary"
        description = desc_match.group(1) if desc_match else response
        
        # Clean escape sequences
        description = description.replace('\\n', '\n').replace('\\"', '"')
        
        return {
            "title": title,
            "description": description
        }