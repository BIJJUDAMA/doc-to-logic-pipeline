"""
File description: Entry point for the structuring pipeline
Purpose: Provides a standard entry script to trigger the full layout and LLM parsing logic
How it works: Simply imports and invokes the run_pipeline function
"""
from src.structuring.pipeline import run_pipeline

if __name__ == "__main__":
    # Execute the main processing pipeline
    run_pipeline()
