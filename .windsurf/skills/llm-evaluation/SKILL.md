# LLM Evaluation Skill

Generic skill for LLM evaluation pipelines - works with images, text documents, or any content.

## Setup

Run `SETUP.md` once to install dependencies in `[WORKSPACE_FOLDER]/.tools/llm-eval-venv/`.

## File Type Detection

Auto-detect by suffix only (no override):
- **Image**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`
- **Text**: `.txt`, `.md`, `.json`, `.py`, `.html`, `.xml`, `.csv`
- **Unknown**: Script exits with error

## Scripts

### call-llm.py - Single LLM Call

```powershell
python call-llm.py --model gpt-4o --input-file photo.jpg --prompt-file prompts/transcribe-page.md
python call-llm.py --model claude-opus-4-20250514 --input-file doc.md --prompt-file prompts/summarize-text.md
```

**Parameters:**
- `--model` - API model ID (required)
- `--input-file` - Input file: image or text
- `--prompt-file` - Prompt file (.md)
- `--output-file` - Output file (default: stdout)
- `--keys-file` - API keys file (default: .env)
- `--write-json-metadata` - Write token usage to separate JSON file

### call-llm-batch.py - Batch Processing

```powershell
python call-llm-batch.py --model gpt-4o --input-folder images/ --output-folder out/ --prompt-file prompts/transcribe-page.md --runs 3 --workers 4
```

**Parameters:**
- `--model` - API model ID (required)
- `--input-folder` - Folder with input files
- `--output-folder` - Folder for output files
- `--prompt-file` - Prompt file (.md)
- `--runs` - Runs per file (default: 1)
- `--workers` - Parallel workers (default: 4)
- `--keys-file` - API keys file (default: .env)

**Features:**
- Parallel processing with configurable workers
- Resume capability (skips existing outputs)
- Incremental save after each item
- Token usage tracking per model

### generate-questions.py - Question Generation

```powershell
python generate-questions.py --model claude-opus-4-20250514 --input-folder images/ --output-file questions.json
```

**Parameters:**
- `--model` - API model ID (required)
- `--input-folder` - Folder with source files
- `--output-file` - Output JSON file
- `--schema-file` - Question schema (default: schemas/default-questions.json)
- `--workers` - Parallel workers (default: 4)

### generate-answers.py - Answer Generation

```powershell
python generate-answers.py --model gpt-5-mini --input-folder transcriptions/ --output-folder answers/ --questions-file questions.json
```

**Parameters:**
- `--model` - API model ID (required)
- `--input-folder` - Folder with processed text files
- `--output-folder` - Folder for answer JSON files
- `--questions-file` - Questions JSON (from generate-questions.py)
- `--workers` - Parallel workers (default: 4)

### evaluate-answers.py - Scoring

```powershell
python evaluate-answers.py --model gpt-5 --input-folder answers/ --output-folder scores/
```

**Parameters:**
- `--model` - Judge model ID (required)
- `--input-folder` - Folder with answer JSON files
- `--output-folder` - Folder for score JSON files
- `--judge-prompt` - Custom judge prompt
- `--pass-threshold` - Pass threshold (default: 4)
- `--workers` - Parallel workers (default: 4)
- `--keys-file` - API keys file (default: .env)

### analyze-costs.py - Cost Analysis

```powershell
python analyze-costs.py --input-folder transcriptions/ --output-file costs.json
```

**Parameters:**
- `--input-folder` - Folder with _token_usage__.json files
- `--output-file` - Output JSON file
- `--pricing` - Custom pricing file (default: model-pricing.json)

## Configuration Files

- `model-registry.json` - Available models with providers and status
- `model-pricing.json` - Token costs per model (USD)
- `schemas/default-questions.json` - Default question categories

## Prompts

- `prompts/transcribe-page.md` - Image transcription
- `prompts/summarize-text.md` - Text summarization
- `prompts/answer-from-text.md` - Question answering
- `prompts/judge-answer.md` - Answer scoring (0-5)

## Pipeline Example

Full evaluation pipeline:

```powershell
$venv = ".tools\llm-eval-venv\Scripts\python.exe"
$skill = ".windsurf\skills\llm-evaluation"

# 1. Transcribe images
& $venv "$skill\call-llm-batch.py" --model gpt-4o --input-folder images/ --output-folder transcriptions/ --prompt-file "$skill\prompts\transcribe-page.md" --runs 3

# 2. Generate questions from original images
& $venv "$skill\generate-questions.py" --model claude-opus-4-20250514 --input-folder images/ --output-file questions.json

# 3. Generate answers from transcriptions
& $venv "$skill\generate-answers.py" --model gpt-5-mini --input-folder transcriptions/ --output-folder answers/ --questions-file questions.json

# 4. Score answers
& $venv "$skill\evaluate-answers.py" --model gpt-5 --input-folder answers/ --output-folder scores/

# 5. Analyze costs
& $venv "$skill\analyze-costs.py" --input-folder transcriptions/ --output-file cost_analysis.json
```

## Key Patterns

**Retry with backoff:**
- 3 retries with exponential backoff (1s, 2s, 4s)
- Skip item after all retries fail

**Atomic writes:**
- Write to `.tmp` file first
- Rename to final on success
- Enables reliable resume

**Logging format:**
```
[ worker_id ] [ x / n ] action...
```

