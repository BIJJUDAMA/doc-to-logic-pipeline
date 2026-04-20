"""
File description: Main script for parallel extraction of PDF document layouts
Purpose: Coordinates the extraction process for multiple PDFs to optimize throughput
How it works: Discovers PDF files in a data directory, and uses a ThreadPoolExecutor to process them concurrently using the parsing Pipeline
"""
import os
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from src.parsing.pipeline import Pipeline
from src.parsing.utils import setup_logger

load_dotenv()
logger = setup_logger(__name__)


# Constants for input and output directories
DATA_DIR = "data"
PARSING_DIR = "output/parsing"

def extract_layout(pdf_path: str, output_dir: str) -> bool:
    # Function to handle layout extraction for a single PDF
    try:
        pipeline = Pipeline()
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f"{os.path.basename(pdf_path)}.json")
        

        # Skip if result file already exists
        if os.path.exists(output_file):
            logger.info(f"Skipping {os.path.basename(pdf_path)}, already exists.")
            return True

        # Perform MinerU parsing and export to JSON
        parsed_doc = pipeline.miner_u_parse(pdf_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(parsed_doc, f, ensure_ascii=False, indent=2)
        logger.info(f"Extraction Complete: {os.path.basename(pdf_path)}")
        return True
        
    except Exception as e:
        logger.error(f"[{os.path.basename(pdf_path)}] Extraction failed: {e}")
        return False

def main():
    # Determine the number of concurrent workers
    workers = int(os.getenv("PARSING_WORKERS", "1"))

    if not os.path.exists(DATA_DIR):
        logger.error(f"Data directory not found: {DATA_DIR}")
        sys.exit(1)

    logger.info(f"Starting Extraction from: {DATA_DIR}")
    pdf_files = [os.path.join(DATA_DIR, f) for f in os.listdir(DATA_DIR) if f.endswith(".pdf")]
    
    if not pdf_files:
        logger.info("No PDF files found.")
        return

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit task for each PDF
        futures = [executor.submit(extract_layout, pdf, PARSING_DIR) for pdf in pdf_files]
        failed = any(not future.result() for future in futures)

    if failed:
        sys.exit(1)

if __name__ == "__main__":
    main()
