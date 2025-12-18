# gemini-2.5-flash-lite

```bash
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses no_defense --limit 200  --debug --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses sandwich --limit 200  --debug --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses instructional --limit 200  --debug --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses xml_tagging --limit 200  --debug --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses signed_prompt --limit 200  --debug --use-laaj
```

# gpt-4.1-mini-2025-04-14

```bash
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses no_defense --limit 200  --debug --model openai:gpt-4.1-mini-2025-04-14 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses sandwich --limit 200  --debug --model openai:gpt-4.1-mini-2025-04-14 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses instructional --limit 200  --debug --model openai:gpt-4.1-mini-2025-04-14 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses xml_tagging --limit 200  --debug --model openai:gpt-4.1-mini-2025-04-14 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses signed_prompt --limit 200  --debug --model openai:gpt-4.1-mini-2025-04-14 --use-laaj
```

# gpt-4.1-mini-2025-04-14 with jatmo

```bash
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses no_defense --scenario Ecommerce --limit 200  --debug --model openai:gpt-4.1-mini-2025-04-14 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses sandwich --scenario Ecommerce --limit 200  --debug --model openai:gpt-4.1-mini-2025-04-14 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses instructional --scenario Ecommerce --limit 200  --debug --model openai:gpt-4.1-mini-2025-04-14 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses xml_tagging --scenario Ecommerce --limit 200  --debug --model openai:gpt-4.1-mini-2025-04-14 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses signed_prompt --scenario Ecommerce --limit 200  --debug --model openai:gpt-4.1-mini-2025-04-14 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses jatmo:ft:gpt-4.1-mini-2025-04-14:miguelfc::CnnyVGzz --scenario Ecommerce --limit 200  --debug --model openai:gpt-4.1-mini-2025-04-14 --use-laaj
``` 

# claude:claude-haiku-4-5-20251001

```bash
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses no_defense --limit 200 --debug --model claude:claude-haiku-4-5-20251001 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses sandwich --limit 200 --debug --model claude:claude-haiku-4-5-20251001 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses instructional --limit 200 --debug --model claude:claude-haiku-4-5-20251001 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses xml_tagging --limit 200 --debug --model claude:claude-haiku-4-5-20251001 --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses signed_prompt --limit 200 --debug --model claude:claude-haiku-4-5-20251001 --use-laaj
```

# huggingface:meta-llama/Llama-3.1-8B-Instruct

```bash
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses no_defense --limit 200 --debug --model huggingface:meta-llama/Llama-3.1-8B-Instruct --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses sandwich --limit 200 --debug --model huggingface:meta-llama/Llama-3.1-8B-Instruct --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses instructional --limit 200 --debug --model huggingface:meta-llama/Llama-3.1-8B-Instruct --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses xml_tagging --limit 200 --debug --model huggingface:meta-llama/Llama-3.1-8B-Instruct --use-laaj
python scripts/run_benchmark.py --dataset=data/combined_dataset.json --defenses signed_prompt --limit 200 --debug --model huggingface:meta-llama/Llama-3.1-8B-Instruct --use-laaj
```
