"""
File description: Main execution pipeline for structuring layouts into LLM intents
Purpose: Iterates over parsed OCR layouts and uses an LLM to derive meaning and metadata
How it works: Reads JSON files from parsing output, groups text blocks using the layout parser, invokes the structure extractor, and validates the output before saving
"""
import os
from tqdm import tqdm
from src.structuring.config import INPUT_DIR, OUTPUT_DIR, INTENT_EXTRACTION_MODE, MULTI_CALL_ENABLED, MULTI_CALL_COUNT
from src.structuring.layout_parser import parse_layout_json
from src.structuring.extractor import extract_intents
from src.structuring.validator import validate_output
from src.structuring.utils import save_json


def run_pipeline():
    # Central pipeline processing function
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\n--- Pipeline Configuration ---")
    print(f"Mode: {'Intent Extraction' if INTENT_EXTRACTION_MODE else 'Zero-Schema'}")
    print(f"Multi-call Enabled: {MULTI_CALL_ENABLED}")
    if MULTI_CALL_ENABLED:
        print(f"Multi-call Count: {MULTI_CALL_COUNT}")
    print(f"------------------------------\n")

    # Collect all previously parsed layout files
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".json")]

    for file in tqdm(files, desc="Processing Files"):
        # Step 1: Check which prompt versions are missing
        num_calls = MULTI_CALL_COUNT if MULTI_CALL_ENABLED else 1
        prompts_to_run = []
        
        base_name = file.split('.')[0]
        
        for i in range(num_calls):
            if MULTI_CALL_ENABLED and num_calls > 1:
                out_file = f"{base_name}_prompt_{i+1}.json"
            else:
                out_file = f"{base_name}.pdf.json"
                
            out_path = os.path.join(OUTPUT_DIR, out_file)
            if not os.path.exists(out_path):
                prompts_to_run.append(i)
        
        if not prompts_to_run:
            print(f"Skipping {file}: All requested prompt versions already exist.")
            continue

        print(f"Processing {file} for prompt versions: {[p+1 for p in prompts_to_run]}")

        # Step 2: Parse layout
        path = os.path.join(INPUT_DIR, file)
        sections = parse_layout_json(path)

        # Initialize storage for the prompt versions we are actually running
        # { prompt_idx: [list_of_results] }
        run_results = {idx: [] for idx in prompts_to_run}

        # Step 3: Extract per section
        for section in sections:
            text = f"{section['title']}\n" + "\n".join(section["content"])

            # Skip very short noise sections
            if len(text.strip()) < 50:
                continue

            # Run for each required prompt version
            for idx in prompts_to_run:
                print(f"  [Prompt {idx+1}] Section: {section['title']}")
                extracted = extract_intents(text, prompt_idx=idx if MULTI_CALL_ENABLED else None)
                
                # Handling mode-specific result structures
                if INTENT_EXTRACTION_MODE:
                    # Expecting one object with intent, facts, etc.
                    run_results[idx].append(extracted)
                else:
                    # ZERO SCHEMA mode: flatten lists of samples
                    if isinstance(extracted, list):
                        run_results[idx].extend(extracted)
                    else:
                        run_results[idx].append(extracted)

        # Step 4: Validate and Save each version
        for idx, results in run_results.items():
            if MULTI_CALL_ENABLED and MULTI_CALL_COUNT > 1:
                final_filename = f"{base_name}_prompt_{idx+1}.json"
            else:
                final_filename = f"{base_name}.pdf.json"

            final_path = os.path.join(OUTPUT_DIR, final_filename)

            # Structure the payload correctly for validation
            if INTENT_EXTRACTION_MODE:
                payload = {"intents": results}
            else:
                payload = results

            final_data = validate_output(payload)
            save_json(final_data, final_path)
            print(f"SUCCESS: Saved {final_filename}")

if __name__ == "__main__":
    run_pipeline()
