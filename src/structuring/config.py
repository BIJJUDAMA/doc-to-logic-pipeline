"""
File description: Configuration module for the structuring pipeline
Purpose: Centralizes the loading of API keys and environment variables needed for LLM structured extraction
How it works: Utilizes python-dotenv to load variables, and exports constants like API keys, model names, and directory paths for other modules to use
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini credentials
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Initialize OpenAI fallback credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4000"))


# Data processing paths
INPUT_DIR = "output/parsing"
OUTPUT_DIR = "output/structuring"
