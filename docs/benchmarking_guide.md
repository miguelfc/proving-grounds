# Benchmarking Guide

This guide explains how to run the automated benchmark suite to test various defenses and LLM models against your dataset. The suite supports both **Direct** (Jailbreak) and **Indirect** (Malicious Content) injection scenarios.

## Prerequisites

Ensure you have generated a dataset first:
```bash
python scripts/generate_dataset.py
```

## Running the Benchmark

Use the `scripts/run_benchmark.py` script to execute tests.

### Basic Usage

Run with default settings (Gemini 1.5 Flash, all defenses, generated dataset):

```bash
python scripts/run_benchmark.py
```

### Specifying Models

You can test multiple models from different providers. Format: `provider:model_name`.

Supported providers: `gemini`, `openai`, `local`.

```bash
python scripts/run_benchmark.py --models gemini:gemini-1.5-flash openai:gpt-3.5-turbo
```

### Specifying Defenses

Choose specific defenses to test.

Available defenses:
- `no_defense`: Baseline (no protection).
- `sandwich`: Sandwich Defense (instructions before and after).
- `instructional`: Instructional Defense (reminders to be helpful/harmless).
- `xml_tagging`: Encloses user input in XML tags.
- `signed_prompt`: Cryptographically signs the system prompt (simulated).

```bash
python scripts/run_benchmark.py --defenses no_defense sandwich xml_tagging
```

### Custom Dataset

Use a specific dataset file (JSON or CSV):

```bash
python scripts/run_benchmark.py --dataset data/my_custom_attacks.csv
```

### Limiting Tests & Disabling Cache

To save costs or run a quick smoke test, you can limit the number of **API calls** (cache misses) and disable caching:

```bash
# Run until 10 new API calls are made (cache hits don't count)
python scripts/run_benchmark.py --limit 10

# Run exactly 10 test cases (since cache is disabled, every case is a miss)
python scripts/run_benchmark.py --limit 10 --no-cache
```

### Error Handling

The benchmark script is designed to **fail fast** on critical errors to prevent wasted API usage or invalid results. Execution will stop immediately if:
- **Authentication Fails**: Missing or invalid API keys.
- **Model Not Found**: The specified model name is incorrect.
- **Rate Limit Exceeded**: The API quota is exhausted (and retries failed).
- **API Connection Error**: Network issues preventing access to the LLM provider.

When an error occurs, the script will:
1.  Log a `CRITICAL ERROR` message with details.
2.  Save any partial results collected so far to a `_PARTIAL.csv` file.
3.  Exit with a non-zero status code.

## Analyzing Results

Results are saved in the `results/` directory (or whatever you specified with `--output`).
Files are named: `results_{provider}_{model}_{defense}.csv`.

Each CSV contains:
- `id`: Test case ID.
- `is_attack`: Whether it was an attack.
- `outcome`: PASS (attack blocked / utility preserved) or FAIL.
- `response`: The model's actual response.
- `latency`: Time taken.

## Example Workflow

1.  **Generate Dataset**:
    ```bash
    python scripts/generate_dataset.py
    ```

2.  **Run Benchmark**:
    ```bash
    python scripts/run_benchmark.py --models gemini:gemini-1.5-flash --defenses all
    ```

3.  **Review Summary**:
    The script prints a summary table at the end of each run showing Attack Success Rate (ASR) and False Positive Rate (FPR).
