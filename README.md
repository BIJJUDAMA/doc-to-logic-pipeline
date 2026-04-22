# Layout Aware Extraction Pipeline

A two-stage, dual-mode pipeline for converting PDF documents into structured knowledge or generic LLM training datasets. Built on layout-aware parsing and LLM-based structuring.

---

## About This Project
<details>
<summary>Click to expand</summary>

This pipeline was originally built to process medical guideline PDFs and produce structured JSON knowledge that a clinical decision-support system could query. Over time, it became clear that the core mechanics (layout parsing, section grouping, and LLM-driven extraction) are domain-agnostic. The same pipeline that extracts clinical facts can generate conversational SFT training data, Q&A datasets, or summaries, just by swapping a prompt and flipping an environment variable. The pipeline in its current shape can be used for medical and non medical documents.

The project now has two operational modes driven by a single env flag (`INTENT_EXTRACTION_MODE`), both built on the same underlying pipeline, making it a general-purpose document-to-dataset engine.

---

## Pipeline Flow

```text
       ┌───────────┐          ┌───────────────────┐          ┌───────────────────┐
       │   INPUT   │          │      STAGE 1      │          │      STAGE 2      │
       │           │          │                   │          │                   │
       │  PDF Docs ├─────────►│ Layout-Aware      ├─────────►│ Semantic          │
       │  (data/)  │          │ Parsing (MinerU)  │          │ Structuring (LLM) │
       └───────────┘          └─────────┬─────────┘          └─────────┬─────────┘
                                        │                              │
                                        ▼                              ▼
                              ┌───────────────────┐          ┌───────────────────┐
                              │   INTERMEDIATE    │          │      FINAL        │
                              │                   │          │                   │
                              │ Layout JSON       │          │ Structured JSON   │
                              │ (output/parsing/) │          │ (output/struct/)  │
                              └───────────────────┘          └───────────────────┘
```

---
</details>

## Project Structure
<details>
<summary>Click to expand</summary>
- `src/parsing/`: Stage 1 - PDF Layout Parsing (GPU required).
- `src/structuring/`: Stage 2 - Intent Structuring using LLMs (Gemini or OpenRouter).
- `data/`: Input PDF directory.
- `output/parsing/`: Intermediate Layout JSON files.
- `output/structuring/`: Final structured JSON results.

---
</details>

## How it Works

<details>
<summary>Click to expand</summary>


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
- **Logic Mapping**: Identifying and structuring conditional logic (if-then-else rules) found in the text.
- **Synthetic Query Generation**: Creates diverse natural language triggers to facilitate downstream search and retrieval.


---
</details>

## Understanding Sections

<details>
<summary>Click to expand</summary>


A "Section" serves as the fundamental unit of work in this pipeline. Rather than processing an entire PDF in one pass, which can cause context loss, output truncation, and increased costs, the system segments the document into logically defined sections for more efficient and reliable handling

### How Sections are Detected
The `layout_parser.py` logic analyzes the intermediate JSON from Stage 1. It identifies a new section whenever it encounters a structural header (e.g., Markdown headers like `#`, or specific layout types like `title` or `h1`). All text, tables, and lists following a header are grouped into that section until the next header is found.

### Why Use Sections?
- **Granular Control**: Each section triggers a separate LLM call. This ensures the model focuses on a manageable chunk of text (typically 1-3 pages), leading to higher extraction density and fewer "missed" facts.
- **Context Preservation**: By grouping tables and lists with their preceding headers, the LLM maintains the semantic context needed to interpret complex data.
- **Scalability**: Large documents (50+ pages) are processed as a series of atomic tasks rather than one monolithic prompt, avoiding LLM context window limits.
- **Deduplication**: In Zero-Schema mode, each section's output is flattened into a final list, ensuring that every part of the document is represented in the resulting dataset without overlap.

</details>

---

## Multi-Call LLM Processing




To improve extraction density and capture diverse perspectives from the same text, the pipeline supports a **Multi-Call** feature. When enabled, each section is processed multiple times by the LLM using different prompt versions.

### How it Works
1.  **Toggle**: Enable this by setting `MULTI_CALL_ENABLED=true` in your `.env`. (Defaults to `false`).
2.  **Versioned Prompts**: In `src/structuring/prompts.json`, each mode can define multiple prompt versions.
3.  **Execution**: When enabled, the pipeline makes `MULTI_CALL_COUNT` calls per section.
4.  **Separated Storage**: 
    - Each prompt version saves its results to a **separate file** if `MULTI_CALL_ENABLED=true`.
    - For `document.pdf`, the outputs will be `document_prompt_1.json`, `document_prompt_2.json`, etc.
    - If multi-call is **disabled**, it defaults to the single `document.pdf.json` filename.

### Why Use Multi-Call?
- **Diverse Extraction**: Different prompts can "nudge" the LLM to focus on different aspects (e.g., one prompt for facts, another for logic, another for edge cases).
- **Higher Recall**: Multiple passes reduce the chance of the LLM missing subtle information in dense text.
- **Dataset Variety**: For SFT data generation, this allows creating multiple unique conversational turns from the same source material.

---

## JSON Repair & Recovery

To handle the inherent variability of LLMs—especially when generating large batches of data that might hit token limits or formatting glitches—the pipeline includes a robust **JSON Repair & Recovery** system.

### Integrated Auto-Repair
When operating in **Zero-Schema Mode** (`INTENT_EXTRACTION_MODE=false`), the pipeline automatically sanitizes and repairs LLM responses before parsing. It is designed to recover from:
- **Truncated Output**: Automatically closes unterminated strings, braces, and brackets if the model cut off mid-sentence.
- **Missing Delimiters**: Fixes missing commas between adjacent JSON objects.
- **Illegal Trailing Commas**: Strips trailing commas that cause standard JSON parsers to fail.

### Standalone Cleaning Utility
For existing outputs or manual recovery, a standalone utility script is provided:

```bash
# Clean and repair a specific file
python scripts/cleaner.py output/structuring/document.json

# Clean all JSON files in a directory
python scripts/cleaner.py output/structuring/
```
This utility will unpack `parse_error` wrappers, recover the raw content, apply repairs, and save the valid structured data back to the file.

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

### Toggleable Prompt Mode

The pipeline supports a **zero‑schema** mode when `INTENT_EXTRACTION_MODE=false`. In this mode:
- The validator no longer enforces the clinical `intent`/`context_packs` schema.
- Output is a flat list of JSON samples, suitable for any dataset (summaries, Q&A, translations, etc.).
- The prompt used is the `zero_schema` entry in `prompts.json`, which can be replaced with any custom prompt.

This toggle is so that the same pipeline can be reused for generic LLM generation without modifying code.
- **Output Schema**: Strict JSON structure including `intents`, `triggers`, and `context_packs`.
- **Medical Logic**: Extraction rules for facts, `if/then/else` decision logic, and source anchoring.
- **Constraint Enforcement**: Mandatory diversity in triggers and strict adherence to provided text (no hallucination).

## Configuration
<details>
<summary>Click to expand</summary>
All configuration is handled via environment variables in the `.env` file.

| Variable | Default | Description |
|---|---|---|
| `INTENT_EXTRACTION_MODE` | `true` | `true` = intent schema mode, `false` = zero-schema dataset generation |
| `MULTI_CALL_ENABLED` | `false` | `true` = Enable multiple LLM calls per section with varied prompts |
| `MULTI_CALL_COUNT` | `3` | Number of LLM calls to make per section if multi-call is enabled |
| `ENABLE_REASONING` | `false` | Enables chain-of-thought reasoning for supported models (e.g. via OpenRouter) |
| `OPENAI_API_KEY` | (none) | API key for OpenRouter or OpenAI-compatible providers |
| `OPENAI_MODEL` | (none) | Model name (e.g. `deepseek/deepseek-v3.2`) |
| `GEMINI_API_KEY` | (none) | Gemini API key, used if OpenAI key is absent |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name |
| `MAX_TOKENS` | `4000` | Max tokens per LLM completion |
| `PARSING_WORKERS` | `1` | Number of parallel workers for Stage 1 parsing |


</details>

## Prompt Engineering for Intent Extraction

<details>
<summary>Click to expand</summary>


When operating in `INTENT_EXTRACTION_MODE=true`, the Stage 2 pipeline enforces a strict schema validation. If you customize `prompt_1`, `prompt_2`, etc., in `src/structuring/prompts.json`, your prompt **must** instruct the LLM to return a JSON object with the following structure to ensure compatibility:

### Required JSON Schema
```json
{
  "intent": "short_snake_case_topic",
  "triggers": [
    "search phrase 1",
    "search phrase 2"
  ],
  "context_packs": [
    {
      "type": "diagnosis | treatment | referral | symptoms | protocol",
      "source_anchor": "section_name",
      "facts": ["atomic fact 1", "atomic fact 2"],
      "contraindications": ["harmful action to avoid"],
      "rules": [
        {
          "if": ["explicit condition"],
          "then": ["explicit outcome"],
          "else": []
        }
      ],
      "decision_trees": {}
    }
  ]
}
```

### Key Components to Include in Your Prompt:
1.  **Core Rules**: Explicitly forbid hallucination and insist on extracting only stated facts.
2.  **Output Format**: Mandatory instruction to return **ONLY** valid JSON without markdown code fences (the pipeline handles stripping fences, but it's safer to request raw JSON).
3.  **Field Definitions**:
    *   `intent`: A single snake_case identifier for the section's topic.
    *   `triggers`: A list of varied phrases a user might use to search for this information.
    *   `context_packs`: An array of knowledge objects. Each must include `facts`, `rules` (conditional logic), and `contraindications`.
4.  **Empty States**: Instruct the LLM to return empty arrays `[]` or objects `{}` if a specific field is not found in the source text, rather than omitting the key.

> **Note**: In Zero-Schema mode (`INTENT_EXTRACTION_MODE=false`), these structural requirements are waived, and the pipeline will accept any valid JSON format the LLM produces.

</details>

---

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


## Setup Models

> [!IMPORTANT]
> Before running Stage 1, ensure all required models are downloaded.

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



---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Credits

Models that make this pipeline possible:

- **[MinerU](https://github.com/opendatalab/MinerU)**: A high-quality, one-stop open-source solution for PDF content extraction.
- **[PDF-Extract-Kit](https://huggingface.co/opendatalab/PDF-Extract-Kit-1.0)**: The core AI model stack (YOLOv8, Layout-Analysis, PaddleOCR, and TableMaster) used for high-fidelity document parsing.
