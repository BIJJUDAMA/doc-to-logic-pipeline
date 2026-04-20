"""
File description: Script to download models from Hugging Face Hub
Purpose: Ensures all necessary machine learning models (like YOLO, OCR, etc.) are available locally before running the pipeline
How it works: Reads the HF_TOKEN from environment, sets up a local model directory, and downloads specific model patterns using snapshot_download
"""
import os
from huggingface_hub import snapshot_download
from dotenv import load_dotenv

def download_models():
    # Determine project root and load environment variables


    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, ".env")
    
    if os.path.exists(env_path):
        print(f"Loading environment from: {env_path}")
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        print(f"Warning: .env file not found at {env_path}")
    
    hf_token = os.getenv("HF_TOKEN")
    
    # Set target local directory for downloaded models


    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    local_dir = os.path.join(project_root, "models")
    
    repo_id = "opendatalab/PDF-Extract-Kit-1.0"
    


    # Specific model patterns to download
    allow_patterns = [
        "models/MFD/YOLO/yolo_v8_ft.pt",
        "models/Layout/YOLO/doclayout_yolo_docstructbench_imgsz1280_2501.pt",
        "models/OCR/paddleocr_torch/*",
        "models/TabRec/TableMaster/*",
        "models/MFR/*"
    ]

    print("--- MinerU Model Downloader ---")
    if hf_token:
        print("Status: Using HF_TOKEN for authenticated download.")
    else:
        print("Status: No HF_TOKEN found. Proceeding with public download.")
    
    print(f"Target: {local_dir}")
    print("This may take several minutes depending on your connection (~5GB total)...")

    try:
        # Execute the model snapshot download
        snapshot_download(
            repo_id=repo_id,
            allow_patterns=allow_patterns,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            token=hf_token
        )
        print("\nSuccess: All models downloaded to ./models/")
        print("You can now start the pipeline with: docker compose up")
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    download_models()
