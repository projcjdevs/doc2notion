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
    
    prompt = f"""You are a professional content analyst creating summaries for a knowledge management system.

Your goal: Transform the document below into a clear, engaging summary that someone can quickly understand and act upon.

WRITING STYLE:
- Write naturally, as if explaining to a colleague
- Avoid phrases like "This document discusses..." or "The document presents..."
- Get straight to the point
- Use active voice and direct language
- Be conversational but professional

STRUCTURE YOUR SUMMARY (300-500 words):

**Overview**
Start directly with what matters. Explain the main topic and why it's important in 2-3 sentences.

**Key Points**
• List the most important information
• Include specific details, numbers, dates, and facts
• Be concrete and actionable
• Use clear, simple language

**Important Details**
• Highlight critical data, statistics, or findings
• Mention deadlines, amounts, or measurements if present
• Note any action items or recommendations

**Conclusion**
End with the main takeaway and any next steps. Keep it brief and actionable.

FORMATTING:
- Use **bold** for section headers only
- Use bullet points (•) for lists
- Keep paragraphs short and scannable
- Write like a human, not a robot

Return ONLY valid JSON:
{{
  "title": "Clear, specific title (5-10 words)",
  "description": "Your natural, engaging summary with proper formatting"
}}

DOCUMENT:
---
{text}
---

JSON Response:"""

    completion = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,  # Slightly higher for more natural language
        max_tokens=2000
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