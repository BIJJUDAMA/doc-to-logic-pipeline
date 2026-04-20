"""
File description: Main execution pipeline for structuring layouts into LLM intents
Purpose: Iterates over parsed OCR layouts and uses an LLM to derive meaning and metadata
How it works: Reads JSON files from parsing output, groups text blocks using the layout parser, invokes the structure extractor, and validates the output before saving
"""
import os
from tqdm import tqdm
from src.structuring.config import INPUT_DIR, OUTPUT_DIR, INTENT_EXTRACTION_MODE
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

        results = []

        # Step 2: Extract per section using LLM
        for section in sections:
            text = f"{section['title']}\n" + "\n".join(section["content"])

            if len(text.strip()) < 50:
                continue

            # Extract data from LLM
            extracted = extract_intents(text)
            
            if INTENT_EXTRACTION_MODE:
                # In intent mode, we expect one object per section
                results.append(extracted)
            else:
                # In ZERO SCHEMA mode, we expect a list of samples; we flatten them
                if isinstance(extracted, list):
                    results.extend(extracted)
                else:
                    results.append(extracted)

        # Step 3: Validate and structure the payload
        if INTENT_EXTRACTION_MODE:
            final_data = validate_output({"intents": results})
        else:
            final_data = validate_output(results)
        
        # Step 4: Save processed result
        save_json(final_data, out_path)

        print(f"Processed: {file}")
