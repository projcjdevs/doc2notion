import os
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
notion = Client(auth=os.getenv("NOTION_API_KEY"))
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

def push(json_data):
    """
    Creates a new page in Notion with title and content.
    """
    properties = {
        "Name": {
            "title": [{"text": {"content": json_data.get("title", "Untitled")}}]
        }
    }

    children = []
    if json_data.get("description"):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{
                    "type": "text",
                    "text": {"content": json_data["description"]}
                }]
            }
        })

    page = notion.pages.create(
        parent={"database_id": DATABASE_ID},
        properties=properties,
        children=children
    )

    return page["id"]