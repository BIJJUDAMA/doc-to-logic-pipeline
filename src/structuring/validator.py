"""
File description: Output validation checks for LLM parsed intents
Purpose: Ensuring standard schema conformance to avoid brittle downstream interactions
How it works: In-place array mutation, walking through structured object elements to fill empty fallback lists or keys
"""
from src.structuring.config import INTENT_EXTRACTION_MODE

def validate_output(data):
    # If in ZEOR SCHEMA mode, bypass the clinical schema validation
    if not INTENT_EXTRACTION_MODE:
        return data

    # Original Clinical Schema Validation
    if "intents" not in data:
        data["intents"] = []
        
    for intent in data.get("intents", []):
        if not isinstance(intent, dict):
            continue

        if "intent" not in intent:
            intent["intent"] = "unknown"

        if "context_packs" not in intent:
            intent["context_packs"] = []

        for pack in intent.get("context_packs", []):
            if not isinstance(pack, dict):
                continue
            if not isinstance(pack.get("facts", []), list):
                pack["facts"] = []

    return data
