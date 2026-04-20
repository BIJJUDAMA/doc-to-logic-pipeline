# Layout Aware Extraction Pipeline

A two-stage, dual-mode pipeline for converting PDF documents into structured clinical knowledge or generic LLM training datasets. Built on layout-aware parsing and LLM-based structuring.

---

## What This Project Is

This pipeline was originally built to process medical guideline PDFs and produce structured JSON knowledge that a clinical decision-support system could query. Over time, it became clear that the core mechanics (layout parsing, section grouping, and LLM-driven extraction) are domain-agnostic. The same pipeline that extracts clinical facts can generate conversational SFT training data, Q&A datasets, or summaries, just by swapping a prompt and flipping an environment variable.

The project now has two operational modes driven by a single env flag (`INTENT_EXTRACTION_MODE`), both built on the same underlying pipeline, making it a general-purpose document-to-dataset engine.

---

## Project Structure

- `src/parsing/`: Stage 1 - PDF Layout Parsing (GPU required).
- `src/structuring/`: Stage 2 - Intent Structuring using LLMs (Gemini or OpenRouter).
- `data/`: Input PDF directory.
- `output/parsing/`: Intermediate Layout JSON files.
- `output/structuring/`: Final structured JSON results.

---

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

---

## The Two Modes

The pipeline operates in one of two modes, controlled by the `INTENT_EXTRACTION_MODE` environment variable.

### Mode 1: Intent Extraction (`INTENT_EXTRACTION_MODE=true`, default)

This is the original clinical mode. It was built to process medical guidelines and produce structured knowledge objects for a downstream retrieval or decision-support system.

**What it does:**
- The LLM is given a strict prompt (`intent_extraction` in `prompts.json`) that enforces an output schema.
- Every section of the document is mapped to an `intent`, which is a short, snake_case topic label.
- It extracts `triggers` (search phrases), `facts` (atomic clinical statements), `rules` (if/then logic), and `contraindications`.
- The validator enforces schema compliance, filling in missing keys with safe defaults.
- Output is wrapped as `{"intents": [...]}`.

**Why this mode exists:**
Clinical decision-support systems need predictable, queryable data. A flat blob of text is useless; structured intents and context packs allow the system to match patient queries to specific clinical rules. The strict schema was a deliberate design choice to ensure the downstream retrieval layer always gets what it expects.

---

### Mode 2: Zero-Schema Generation (`INTENT_EXTRACTION_MODE=false`)

This mode turns the pipeline into a **generic LLM dataset generator**. It was introduced because the document ingestion and section-grouping logic in Stage 1 is valuable regardless of what you want to do with the text. By removing the schema constraint entirely, the pipeline becomes reusable for any task.

**What it does:**
- The LLM is given the `zero_schema` prompt from `prompts.json`, which can be any instruction set: SFT data generation, summarization, Q&A extraction, translation, and more.
- The validator is a no-op; whatever valid JSON the model returns is accepted.
- Results from each section are flattened into a single list, giving you a clean, training-ready dataset file per PDF.

**Why this mode exists:**
The schema enforcement that makes Mode 1 reliable also makes it rigid. For dataset generation, that rigidity is a liability because you want the LLM to produce whatever structure fits your training format. Zero-schema mode removes that constraint while reusing all the parsing infrastructure of Stage 1.

**Swapping the task:** To use this mode for a different task (e.g., summarization instead of SFT), simply replace the `zero_schema` prompt in `src/structuring/prompts.json`. No code changes needed.

---

## Configuration

All configuration is handled via environment variables in the `.env` file.

| Variable | Default | Description |
|---|---|---|
| `INTENT_EXTRACTION_MODE` | `true` | `true` = clinical schema mode, `false` = zero-schema dataset generation |
| `ENABLE_REASONING` | `false` | Enables chain-of-thought reasoning for supported models (e.g. via OpenRouter) |
| `OPENAI_API_KEY` | (none) | API key for OpenRouter or OpenAI-compatible providers |
| `OPENAI_MODEL` | (none) | Model name (e.g. `deepseek/deepseek-v3.2`) |
| `GEMINI_API_KEY` | (none) | Gemini API key, used if OpenAI key is absent |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `MAX_TOKENS` | `4000` | Max tokens per LLM completion |
| `PARSING_WORKERS` | `1` | Number of parallel workers for Stage 1 parsing |


## Opinionated Directory Structure

The pipeline follows a strict, opinionated directory structure for seamless data flow:

- **`data/`**: The input directory. Place all PDF files to be processed here.
- **`output/parsing/`**: Stage 1 output. Contains layout-aware JSON files generated from the PDFs.
- **`output/structuring/`**: Stage 2 output. Contains the final structured clinical knowledge in JSON format.
- **`models/`**: Stores the required local model weights for the parsing engine.

All results are automatically namespaced by their respective stage within the `output/` directory.

## Opinionated Knowledge Structuring (`prompts.json`)

Stage 2 uses an opinionated prompting system defined in `src/structuring/prompts.json`. This file holds two prompt templates:

- **`intent_extraction`**: The clinical schema prompt. Enforces strict JSON output with `intent`, `triggers`, `context_packs`, `facts`, `rules`, and `contraindications`.
- **`zero_schema`**: The generic dataset generation prompt. Currently configured for ASHA worker conversational SFT data but can be replaced with any task-specific instruction.

### Toggleable Prompt Mode

The pipeline supports a **zero‑schema** mode when `INTENT_EXTRACTION_MODE=false`. In this mode:
- The validator no longer enforces the clinical `intent`/`context_packs` schema.
- Output is a flat list of JSON samples, suitable for any dataset (summaries, Q&A, translations, etc.).
- The prompt used is the `zero_schema` entry in `prompts.json`, which can be replaced with any custom prompt.

This toggle is so that the same pipeline can be reused for generic LLM generation without modifying code.
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
