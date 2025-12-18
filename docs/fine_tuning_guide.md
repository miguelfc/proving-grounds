# Fine-tuning Guide for Jatmo Defense

This guide explains how to fine-tune models for the Jatmo defense strategy across different providers.

## Overview

Jatmo (Just Another Task-specific Model Optimization) uses a fine-tuned model trained on legitimate task interactions to resist prompt injection attacks. The model learns to recognize and respond appropriately to normal banking/ecommerce requests while ignoring malicious instructions.

## Prerequisites

- API key for your chosen provider (OpenAI, Google, Anthropic)
- Training data (at least 50-100 examples, ideally 500+)
- Python 3.8+ with provider-specific packages

---

## OpenAI Fine-tuning

### Step 1: Prepare Training Data

Training data must be in JSONL format:

```jsonl
{"messages": [{"role": "system", "content": "You are a helpful Banking Assistant..."}, {"role": "user", "content": "Check my balance"}, {"role": "assistant", "content": "TOOL_CALL: check_balance()"}]}
{"messages": [{"role": "system", "content": "You are a helpful Banking Assistant..."}, {"role": "user", "content": "Transfer $100 to Alice"}, {"role": "assistant", "content": "TOOL_CALL: transfer_money('Alice', 100)"}]}
```

Generate training data:
```bash
python scripts/generate_training_data.py --output training_data.jsonl
```

### Step 2: Upload & Start Fine-tuning (Automated)

We provide a helper script to handle file upload and job creation automatically.

```bash
python scripts/fine_tuning/start_openai_finetune.py --file training_data.jsonl --model gpt-4.1-mini-2025-04-14
```

This will:
1. Upload the file to OpenAI.
2. Wait for processing.
3. Start the fine-tuning job.
4. Output the **Job ID** and **Model ID**.

### Step 3: Monitor Training

You can check the status using the Job ID returned by the script:

```bash
openai api fine_tuning.jobs.retrieve -i ftjob-xyz789
```

Training typically takes 10-60 minutes depending on dataset size.

### Step 5: Use Fine-tuned Model

```python
from src.framework.defenses import JatmoDefense

defense = JatmoDefense(model_id="ft:gpt-3.5-turbo:org:banking-jatmo:abc123")
```

**Cost:** ~$0.008 per 1K tokens (training), same as base model (inference)

---

## Google Gemini Fine-tuning

### Step 1: Prepare Training Data

Gemini uses a different format. Create a CSV or JSONL file:

```bash
python scripts/generate_training_data.py --provider gemini --output gemini_training.jsonl
```

### Step 2: Fine-tune via Google Cloud / AI Studio

*Note: The AI Studio interface changes frequently. Please refer to legitimate Google Cloud Vertex AI or AI Studio documentation for the most up-to-date fine-tuning workflow.*

1. Go to [Google AI Studio](https://aistudio.google.com/) or Google Cloud Console.
2. Look for **Tuned Models** or **Vertex AI Fine-tuning**.
3. Create a new tuning job and upload your `gemini_training.jsonl`.
4. Select a base model (e.g., `gemini-1.5-flash`).

### Step 3: Use Fine-tuned Model

Once tuning completes, you'll get a model name like `tunedModels/banking-jatmo-abc123`:

```python
from src.llm import GeminiClient
from src.framework.defenses import JatmoDefense

# Create client with fine-tuned model
client = GeminiClient(model_name="tunedModels/banking-jatmo-abc123")
defense = JatmoDefense(model_id="tunedModels/banking-jatmo-abc123")
```

**Cost:** Free for limited tuning, paid for production use

---

## Anthropic Claude Fine-tuning

Claude supports fine-tuning through their API (currently in beta).

### Step 1: Prepare Training Data

```bash
python scripts/generate_training_data.py --provider claude --output claude_training.jsonl
```

### Step 2: Fine-tune via Anthropic API

```python
from anthropic import Anthropic

client = Anthropic(api_key="your-api-key")

# Upload training data
file_response = client.files.create(
    file=open("claude_training.jsonl", "rb"),
    purpose="fine-tune"
)

# Create fine-tuning job
job = client.fine_tuning.create(
    training_file=file_response.id,
    model="claude-3-haiku-20240307",
    suffix="banking-jatmo"
)
```

### Step 3: Use Fine-tuned Model

```python
from src.framework.defenses import JatmoDefense

defense = JatmoDefense(model_id="ft:claude-3-haiku:org:banking-jatmo:abc123")
```

---

## Local Model Fine-tuning (HuggingFace)

For open-source models like Llama, Mistral, or Phi.

### Step 1: Install Dependencies

```bash
pip install transformers datasets peft accelerate bitsandbytes
```

### Step 2: Prepare Training Data

```bash
# Generate data in HuggingFace format
python scripts/generate_training_data.py --provider huggingface --output training_dataset.jsonl
```

Then load it in your training script:
```python
from datasets import load_dataset

dataset = load_dataset("json", data_files="training_dataset.jsonl")
```

### Step 3: Fine-tune with LoRA

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

# Load base model
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-chat-hf")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-chat-hf")

# Configure LoRA
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)

# Training
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset,
    tokenizer=tokenizer,
    max_seq_length=512,
    args=TrainingArguments(
        output_dir="./llama-banking-jatmo",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        save_steps=100
    )
)

trainer.train()
trainer.save_model("./llama-banking-jatmo")
```

### Step 4: Use Fine-tuned Model

```python
from src.llm import create_client
from src.framework.defenses import JatmoDefense

client = create_client("huggingface", "./llama-banking-jatmo")
defense = JatmoDefense(model_id="./llama-banking-jatmo")
```

**Cost:** Free (compute only)

---

## Best Practices (All Providers)

1. **Diverse Training Data**: 500+ examples covering various use cases
2. **Attack Examples**: Include injection attempts with proper refusals (30-40% of dataset)
3. **Validation Set**: Hold out 10-20% for evaluation
4. **Iterative Refinement**: Fine-tune multiple times with improved data
5. **Monitor Metrics**: Track ASR (Attack Success Rate) and FPR (False Positive Rate)

## Comparison Table

| Provider | Models | Cost (Training) | Cost (Inference) | Time | Difficulty |
|----------|--------|-----------------|------------------|------|------------|
| **OpenAI** | GPT-3.5, GPT-4o | $0.008/1K tokens | Same as base | 10-60 min | Easy |
| **Gemini** | 1.5 Flash, Pro | Free/Paid | Same as base | 30-120 min | Easy |
| **Claude** | 3 Haiku, Sonnet | TBD (Beta) | Same as base | TBD | Medium |
| **Local** | Llama, Mistral | Free (GPU) | Free | 1-4 hours | Hard |

## Troubleshooting

**Training fails:**
- Check data format (provider-specific)
- Ensure sufficient examples (50+ minimum)
- Verify API keys and permissions

**Poor performance:**
- Increase dataset size (aim for 500+)
- Balance attack/legitimate examples
- Add more diverse attack patterns
- Try different base models

## Next Steps

After fine-tuning:
1. Test with `scripts/run_benchmark.py`
2. Compare ASR/FPR against baseline
3. Iterate on training data if needed
4. Deploy to production
