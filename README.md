# Layout Aware Extraction Pipeline

A two-stage pipeline for converting PDF guidelines into structured knowledge using layout-aware parsing and intent structuring.

## Project Structure

- `src/parsing/`: Stage 1 - PDF Layout Parsing (GPU required).
- `src/structuring/`: Stage 2 - Intent Structuring using LLMs (Gemini or OpenRouter).
- `data/`: Input PDF directory.
- `output/parsing/`: Intermediate Layout JSON files.
- `output/structuring/`: Final structured JSON results.

## How it Works

The pipeline transforms unstructured documents into high-fidelity structured data through two distinct phases:

### 1. Layout-Aware Parsing (Structural Intelligence)
Unlike traditional PDF-to-text tools that lose document hierarchy, this stage uses a deep-learning-based parsing engine to analyze the visual layout. It identifies:
- **Hierarchical Sections**: Automatically detects headings, sub-headings, and their relationship to body text.
- **Complex Elements**: Extracts tables and lists while maintaining their structural integrity.
- **Document Mapping**: Produces a structured intermediate JSON that preserves the "reading order" and logical grouping of information.

### 2. Semantic Structuring (Cognitive Extraction)
The second stage uses Large Language Models to interpret the structured text segments. It applies a schema-driven approach to:
- **Intent Identification**: Classifies the core purpose of each section into specific topics.
- **Atomic Fact Extraction**: Distills complex paragraphs into discrete, verifiable facts.
- **Logic Mapping**: Identifies and structures conditional logic (if-then-else rules) found in the text.
- **Synthetic Query Generation**: Creates diverse natural language triggers to facilitate downstream search and retrieval.

## Configuration
...
All configuration is handled via environment variables in the `.env` file.


## Opinionated Directory Structure

The pipeline follows a strict, opinionated directory structure for seamless data flow:

- **`data/`**: The input directory. Place all PDF files to be processed here.
- **`output/parsing/`**: Stage 1 output. Contains layout-aware JSON files generated from the PDFs.
- **`output/structuring/`**: Stage 2 output. Contains the final structured clinical knowledge in JSON format.
- **`models/`**: Stores the required local model weights for the parsing engine.

All results are automatically namespaced by their respective stage within the `output/` directory.

## Opinionated Knowledge Structuring (`prompts.json`)

Stage 2 uses an opinionated prompting system defined in `src/structuring/prompts.json`. This file governs:
- **Output Schema**: Strict JSON structure including `intents`, `triggers`, and `context_packs`.
- **Medical Logic**: Extraction rules for facts, `if/then/else` decision logic, and source anchoring.
- **Constraint Enforcement**: Mandatory diversity in triggers and strict adherence to provided text (no hallucination).


## Running with Docker

The entire pipeline is orchestrated via Docker Compose.

### Build and run everything
```powershell
docker compose up --build
```

### Stage-wise Building
If you only need to build a specific stage:
```powershell
# Build only the Parsing stage
docker compose build layout-parser

# Build only the Structuring stage
docker compose build intent-structurer
```

## Running Stages Individually

If you prefer to run only one stage of the pipeline at a time:

### Stage 1: Parsing
To run only the layout parsing stage:
```powershell
docker compose run --rm layout-parser
```

### Stage 2: Structuring
To run only the intent structuring stage (requires existing parsing results in `output/parsing/`):
```powershell
docker compose run --rm intent-structurer
```

## Setup Models

Before running Stage 1, ensure the required models are downloaded:

```bash
# 1. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# Unix/macOS
source venv/bin/activate

# 2. Install downloader dependencies
pip install huggingface-hub python-dotenv

# 3. Run the download script
python scripts/download_models.py
```
