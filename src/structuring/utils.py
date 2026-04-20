"""
File description: Utility script containing simple helper functions for the structuring engine
Purpose: Keeps file I/O operations consistent throughout the project directory
How it works: Currently provides a wrapper around the json payload dumping to enforce encoding standards
"""
import json


def save_json(data, path):
    # Saves generic data objects out to a formatted JSON footprint
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
