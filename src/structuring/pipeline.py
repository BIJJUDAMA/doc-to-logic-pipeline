"""
File description: Main execution pipeline for structuring layouts into LLM intents
Purpose: Iterates over parsed OCR layouts and uses an LLM to derive meaning and metadata
How it works: Reads JSON files from parsing output, groups text blocks using the layout parser, invokes the structure extractor, and validates the output before saving
"""
import os
from tqdm import tqdm
from src.structuring.config import INPUT_DIR, OUTPUT_DIR
from src.structuring.layout_parser import parse_layout_json
from src.structuring.extractor import extract_intents
from src.structuring.validator import validate_output
from src.structuring.utils import save_json


def run_pipeline():
    # Central pipeline processing function
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Collect all previously parsed layout files
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".json")]

    for file in tqdm(files):
        out_path = os.path.join(OUTPUT_DIR, file)

        if os.path.exists(out_path):
            print(f"Skipping {file} as it has already been processed.")
            continue

        path = os.path.join(INPUT_DIR, file)
        # Step 1: Layout to Sections
        sections = parse_layout_json(path)

        all_intents = []

        # Step 2: Extract per section using LLM
        for section in sections:
            text = f"{section['title']}\n" + "\n".join(section["content"])

            if len(text.strip()) < 50:
                continue

            result = extract_intents(text)
            all_intents.append(result)

        # Step 3: Validate and structure the payload
        validated = validate_output({"intents": all_intents})
        
        # Step 4: Save processed result
        save_json(validated, out_path)

        print(f"Processed: {file}")

