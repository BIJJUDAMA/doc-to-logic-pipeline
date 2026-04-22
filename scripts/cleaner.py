"""
File description: Standalone utility for cleaning and repairing LLM-generated JSON files
Purpose: Fixes common formatting issues (missing brackets, markdown fences, sequences of objects) in existing JSON output files
Usage: python scripts/cleaner.py <file_or_directory_path>
"""
import os
import json
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.structuring.cleaner import clean_text_content

def process_file(file_path):
    print(f"Checking {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if this is a 'parse_error' wrapper
        is_parse_error = False
        raw_text = ""
        
        if isinstance(data, list) and len(data) == 1:
            if isinstance(data[0], dict) and data[0].get("intent") == "parse_error":
                is_parse_error = True
                raw_text = data[0].get("raw", "")
        elif isinstance(data, dict) and data.get("intent") == "parse_error":
            is_parse_error = True
            raw_text = data.get("raw", "")

        if is_parse_error and raw_text:
            print(f"  -> Found parse_error wrapper. Attempting to recover raw content...")
            cleaned = clean_text_content(raw_text)
            try:
                final_data = json.loads(cleaned)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(final_data, f, indent=2)
                print(f"  [SUCCESS] Recovered and cleaned {file_path}")
            except Exception as e:
                print(f"  [FAILED] Could not parse recovered text: {e}")
        else:
            print(f"  [SKIP] File appears to be valid already.")

    except json.JSONDecodeError:
        print(f"  -> File is not valid JSON. Attempting direct string cleanup...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            cleaned = clean_text_content(content)
            final_data = json.loads(cleaned)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, indent=2)
            print(f"  [SUCCESS] Cleaned and converted {file_path}")
        except Exception as e:
            print(f"  [FAILED] Could not clean raw file: {e}")
    except Exception as e:
        print(f"  [ERROR] {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/cleaner.py <file_or_directory>")
        sys.exit(1)
    
    path = sys.argv[1]
    if os.path.isfile(path):
        process_file(path)
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.json'):
                    process_file(os.path.join(root, file))
    else:
        print(f"Path not found: {path}")
