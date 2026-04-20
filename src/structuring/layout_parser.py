"""
File description: Parsing and grouping layout structures
Purpose: Groups individual lines of extracted text into logical sections based on headers
How it works: Traverses over layout-parsed JSON outputs, checking object types or string formats, and appends them to current titled sections appropriately
"""
import json


def group_sections(content_list):
    # Groups unstructured blocks into logical document sections

    sections = []
    current = {"title": "Introduction", "content": []}

    for item in content_list:

        if isinstance(item, list):
            for sub in item:
                process_item(sub, current, sections)
        else:
            process_item(item, current, sections)

    if current["content"]:
        sections.append(current)

    return sections

def process_item(item, current, sections):
    # Determines type of block and aggregates it beneath a common header
    if isinstance(item, str):
        text = item.strip()
        if not text:
            return
        

        # Handle markdown style headings like '# Header'
        if text.startswith("#"):
            if current["content"]:
                sections.append(current.copy())
            current["title"] = text.lstrip("#").strip()
            current["content"] = []
        else:
            current["content"].append(text)
        return

    if not isinstance(item, dict):
        return

    text = item.get("text", "").strip()
    if not text:
        return


    item_type = item.get("type", "").lower()
    
    # Handle document style properties
    if "title" in item_type or item_type.startswith("h"):
        if current["content"]:
            sections.append(current.copy())
        current["title"] = text
        current["content"] = []
    else:
        current["content"].append(text)


def parse_layout_json(path):
    # Main entrypoint to read layout file and run grouping
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)


    content_list = data.get("content_list", [])
    
    return group_sections(content_list)
