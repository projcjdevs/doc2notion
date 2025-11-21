import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
notion = Client(auth=os.getenv("NOTION_API_KEY"))
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def push(json_data, file_path=None):
    """
    Creates a new page in Notion with title and formatted content.
    Automatically splits long text into chunks to respect Notion's 2000 char limit.
    """
    properties = {
        "Name": {
            "title": [{"text": {"content": json_data.get("title", "Untitled")}}]
        }
    }

    children = []
    
    # Add file reference if provided
    if file_path and os.path.exists(file_path):
        file_name = os.path.basename(file_path)
        children.append({
            "object": "block",
            "type": "callout",
            "callout": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": f"📎 Source: {file_name}"},
                    "annotations": {"bold": True}
                }],
                "icon": {"emoji": "📄"},
                "color": "blue_background"
            }
        })
        
        children.append({
            "object": "block",
            "type": "divider",
            "divider": {}
        })
    
    # Parse and format the description
    if json_data.get("description"):
        description = json_data["description"]
        
        # Split into sections by double newlines
        sections = description.split('\n\n')
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Check if it's a header (starts with **)
            if section.startswith('**') and section.count('**') >= 2:
                # Extract header text
                header_end = section.find('**', 2)
                if header_end != -1:
                    header_text = section[2:header_end]
                    remaining_text = section[header_end+2:].strip()
                    
                    # Add as heading
                    children.append({
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": header_text[:2000]}  # Limit header too
                            }]
                        }
                    })
                    
                    # Add remaining text if any (with chunking)
                    if remaining_text:
                        add_text_chunks(children, remaining_text)
            
            # Check if it's a bullet point section
            elif section.startswith('•') or section.startswith('-'):
                lines = section.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('•') or line.startswith('-'):
                        bullet_text = line.lstrip('•-').strip()
                        # Split long bullets into chunks
                        if len(bullet_text) > 2000:
                            chunks = split_text(bullet_text, 2000)
                            for chunk in chunks:
                                children.append({
                                    "object": "block",
                                    "type": "bulleted_list_item",
                                    "bulleted_list_item": {
                                        "rich_text": [{
                                            "type": "text",
                                            "text": {"content": chunk}
                                        }]
                                    }
                                })
                        else:
                            children.append({
                                "object": "block",
                                "type": "bulleted_list_item",
                                "bulleted_list_item": {
                                    "rich_text": [{
                                        "type": "text",
                                        "text": {"content": bullet_text}
                                    }]
                                }
                            })
            
            # Regular paragraph - needs chunking!
            else:
                add_text_chunks(children, section)

    page = notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties=properties,
        children=children
    )

    return page["id"]


def split_text(text, max_length=2000):
    """
    Split text into chunks of max_length, trying to break at sentence boundaries.
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by sentences (periods followed by space)
    sentences = text.replace('. ', '.|').split('|')
    
    for sentence in sentences:
        # If adding this sentence would exceed limit, save current chunk
        if len(current_chunk) + len(sentence) > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # Single sentence is too long, force split
                chunks.append(sentence[:max_length])
                current_chunk = sentence[max_length:]
        else:
            current_chunk += sentence
    
    # Add remaining text
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def add_text_chunks(children, text):
    """
    Add text to children, splitting into multiple paragraphs if needed.
    """
    chunks = split_text(text, 2000)
    
    for chunk in chunks:
        if chunk.strip():
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{
                        "type": "text",
                        "text": {"content": chunk}
                    }]
                }
            })