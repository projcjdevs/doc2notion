from ocr_extract import extract_text
from parse_groq import parse_to_json
from push2notion import push

def doc_to_notion(path):
    print("🔍 Extracting OCR…")
    text = extract_text(path)
    print(f"📄 Extracted text ({len(text)} chars):\n{text[:200]}...\n")

    print("🤖 Parsing JSON via Groq…")
    data = parse_to_json(text)
    print(f"✏️  Title: {data['title']}")
    print(f"📝 Description: {data['description'][:100]}...\n")

    print("📤 Pushing to Notion…")
    page_id = push(data)

    print(f"✅ Done! Created Notion page: {page_id}")

if __name__ == "__main__":
    doc_to_notion("Screenshot 2025-11-17 124121.png")
