# Proving Grounds: Prompt Injection Benchmarking Framework

Proving Grounds is a modular Python-based framework designed to evaluate the robustness of Large Language Models (LLMs) against **Direct** and **Indirect** Prompt Injection (PI) attacks, and to benchmark the effectiveness of various mitigation strategies.

It uses a **Unified Agent Simulation** approach, where every test case (whether a direct prompt or an indirect injection via email/reviews) is executed by an Agent in a persistent environment. This allows for realistic verification of attacks, measuring success not just by text output but by **state changes** (e.g., unauthorized money transfers, data exfiltration).

## Documentation Map

The documentation is organized by use case. Start here to find the guide you need:

| Goal | Guide | Description |
|------|-------|-------------|
| **Run Tests** | [Benchmarking Guide](docs/benchmarking_guide.md) | **Start Here.** How to run the automated benchmark suite across different models and defenses. |
| **Create Data** | [Dataset Generation Guide](docs/dataset_generation_guide.md) | How to generate large, synthetic datasets using combinatorial YAML configurations. |
| **Manual Tests** | [Custom Datasets Guide](docs/custom_datasets_guide.md) | How to create specific, hand-crafted test cases (JSON/CSV) for targeted testing. |
| **Advanced Defense** | [Fine-tuning Guide](docs/fine_tuning_guide.md) | How to implement the "Jatmo" defense by fine-tuning models on safe/unsafe examples. |

## Quick Start

1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up API Keys**:
    Create a `.env` file (see `.env.example` for details):
    ```bash
    OPENAI_API_KEY=your_key
    GEMINI_API_KEY=your_key
    ANTHROPIC_API_KEY=your_key
    HUGGINGFACE_API_KEY=your_key
    ```

3.  **Run the Benchmark**:
    ```bash
    python scripts/run_benchmark.py
    ```
    This runs the default test suite using Gemini 1.5 Flash.

## Key Features

*   **Unified Agent Testing**: Test both **Direct** (Jailbreaks) and **Indirect** (Malicious Content) injections using the same pipeline.
*   **Multi-Provider Support**: Use OpenAI, Gemini, Claude, or local HuggingFace models via a unified interface.
*   **Modular Architecture**:
    *   **Defenses**: Pluggable strategies in `src/framework/defenses/` (Sandwich, Signed Prompt, Perplexity Detection, **Jatmo**).
    *   **Environments**: Pluggable worlds in `src/framework/environments/` (Banking, Ecommerce).
*   **LLM Caching**: Built-in caching system (`llm_cache.json`) to reduce API costs and latency.

## Advanced Usage

### 1. Generating Datasets
To create a comprehensive benchmark, generate a synthetic dataset:
```bash
python scripts/generate_dataset.py
```
Once generated, you can run the benchmark using this dataset:
```bash
python scripts/run_benchmark.py --dataset data/generated_dataset.json
```
See [Dataset Generation Guide](docs/dataset_generation_guide.md) for configuration details.

### 2. Running Custom Benchmarks
Run specific models and defenses:
```bash
python scripts/run_benchmark.py --models openai:gpt-4o-mini --defenses sandwich xml_tagging
```
See [Benchmarking Guide](docs/benchmarking_guide.md) for full options.

**Batch Testing:**
```bash
python scripts/run_benchmark.py --dataset examples/banking_attacks.json
python scripts/run_benchmark.py --dataset my_tests.json --models openai:gpt-4o-mini
```

### 3. Fine-tuning (Jatmo Defense)
Train a model to distinguish between safe and unsafe prompts:
```bash
# 1. Generate training data
python scripts/generate_training_data.py --provider openai

# 2. Start fine-tuning job (automated)
python scripts/fine_tuning/start_openai_finetune.py --file jatmo_train.jsonl --model gpt-4o-mini
```
See [Fine-tuning Guide](docs/fine_tuning_guide.md) for the complete workflow.

### 4. Scenario Filtering
Test a specific domain (e.g., Banking or Ecommerce) to focus your benchmark:
```bash
python scripts/run_benchmark.py --scenario Ecommerce --models openai:gpt-4o-mini
```
This runs only the Ecommerce test cases and tags the results file accordingly.

## Project Structure

```
proving-grounds/
├── src/
│   ├── framework/
│   │   ├── defenses/          # Defense strategies (Sandwich, XML, Jatmo, etc.)
│   │   ├── environments/      # Simulated worlds (Banking, Ecommerce)
│   │   │   ├── base/          # Base classes
│   │   │   ├── banking/       # Banking environment & tools
│   │   │   └── ecommerce/     # Ecommerce environment & tools
│   │   ├── agent.py           # Agent implementation
│   │   └── runner.py          # Test orchestration
│   └── llm_client.py          # LLM provider implementations
├── scripts/
│   ├── run_benchmark.py       # Main benchmarking script
│   ├── generate_dataset.py    # Synthetic dataset generator
│   ├── generate_training_data.py # Fine-tuning data generator
│   └── fine_tuning/           # Fine-tuning helper scripts
│       └── start_openai_finetune.py
├── data/
│   └── dataset_config/        # YAML configs for dataset generation
└── docs/                      # Documentation guides
```

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.
