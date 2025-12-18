#!/usr/bin/env python3
"""
Benchmark Script
Runs the prompt injection benchmark across multiple models and defenses.
"""
import argparse
import os
import sys
import time
import datetime
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.framework.datasets import FileDataset, JSONDataset
from src.framework.runner import TestRunner
from src.framework.evaluator import Evaluator
from src.framework.logger import logger
from src.llm import create_client, LLMError
from src.framework.defenses import (
    NoDefense,
    SandwichDefense,
    InstructionalDefense,
    XMLTaggingDefense,
    SignedPromptDefense,
    CompositeDefense,
    JatmoDefense,
)


def create_defense(name: str):
    name = name.lower().strip()
    if name == "no_defense":
        return NoDefense()
    elif name == "sandwich":
        return SandwichDefense()
    elif name == "instructional":
        return InstructionalDefense()
    elif name == "xml_tagging":
        return XMLTaggingDefense()
    elif name == "signed_prompt":
        return SignedPromptDefense()
    elif name.startswith("jatmo:"):
        model_id = name.split(":", 1)[1]
        return JatmoDefense(model_id=model_id)
    else:
        print(f"Warning: Unknown defense '{name}'")
        return None


def get_defenses(defense_names: List[str]):
    defenses = []

    # Flatten list (handle commas)
    flat_names = []
    for d in defense_names:
        flat_names.extend(d.split(","))

    for name in flat_names:
        name = name.strip()
        if not name:
            continue

        if name == "all":
            defenses.extend(
                [
                    NoDefense(),
                    SandwichDefense(),
                    InstructionalDefense(),
                    XMLTaggingDefense(),
                    SignedPromptDefense(),
                ]
            )
            continue

        if "+" in name:
            # Composite Defense
            sub_names = name.split("+")
            sub_defenses = []
            for sub in sub_names:
                d = create_defense(sub)
                if d:
                    sub_defenses.append(d)
            if sub_defenses:
                defenses.append(CompositeDefense(sub_defenses))
        else:
            # Single Defense
            d = create_defense(name)
            if d:
                defenses.append(d)

    return defenses


def run_benchmark(
    dataset_path: str,
    models: List[str],
    defense_names: List[str],
    output_dir: str,
    limit: int = None,
    use_cache: bool = True,
    debug: bool = False,
    use_laaj: bool = False,
    scenario: str = None,
):
    logger.start_execution()

    # 1. Load Dataset
    print(f"Loading dataset from {dataset_path}...")
    if dataset_path.endswith(".json"):
        dataset = JSONDataset(dataset_path)
    else:
        dataset = FileDataset(dataset_path)

    # Note: We no longer slice the dataset here.
    # The limit is passed to the runner to control API usage.

    print(f"Loaded {len(dataset)} test cases.")

    # Apply Scenario Filter
    if scenario:
        dataset.filter_by_scenario(scenario)

    # 2. Setup Output
    os.makedirs(output_dir, exist_ok=True)

    # 3. Iterate Models
    for model_config in models:
        provider, model_name = model_config.split(":")
        print(f"\n\n=== Testing Model: {model_name} ({provider}) ===")

        # Load Rate Limits
        import yaml

        rate_limits = {}
        try:
            with open("data/dataset_config/rate_limits.yaml", "r") as f:
                rate_limits = yaml.safe_load(f)
        except FileNotFoundError:
            print(
                "Warning: data/dataset_config/rate_limits.yaml not found. Proceeding without rate limits."
            )

        # Determine Rate Limit
        rpm_limit = None
        if provider in rate_limits:
            provider_limits = rate_limits[provider]
            if model_name in provider_limits:
                rpm_limit = provider_limits[model_name]
            elif "default" in provider_limits:
                rpm_limit = provider_limits["default"]

        if rpm_limit:
            print(f"Applying rate limit: {rpm_limit} RPM for {model_name}")

        try:
            client = create_client(
                provider, model_name, use_cache=use_cache, rpm_limit=rpm_limit
            )
        except Exception as e:
            print(f"Failed to initialize client for {model_name}: {e}")
            continue

        evaluator = Evaluator(use_laaj=use_laaj)
        runner = TestRunner(client, evaluator)

        # 4. Iterate Defenses
        defenses = get_defenses(defense_names)

        for defense in defenses:
            defense_name = defense.__class__.__name__
            print(f"\n--- Running Defense: {defense_name} ---")

            # Base System Prompt
            system_prompt = None

            # Clear previous results
            runner.results = []

            # Pass limit to runner
            try:
                runner.run(dataset, defense, system_prompt, limit=limit, debug=debug)
            except LLMError as e:
                logger.log(f"CRITICAL ERROR: {e}")
                logger.log("Stopping execution as requested.")

                # Save partial results
                dataset_name = os.path.splitext(os.path.basename(dataset_path))[0]
                date_str = datetime.datetime.now().strftime("%Y-%m-%d")

                base_filename = f"results_{date_str}_{dataset_name}_{provider}_{model_name.replace('/', '_')}_{defense_name}_PARTIAL"
                csv_file = os.path.join(output_dir, f"{base_filename}.csv")
                md_file = os.path.join(output_dir, f"{base_filename}.md")

                runner.save_results(csv_file)
                runner.save_summary(md_file)
                runner.print_summary()

                sys.exit(1)

            # Save Results
            # Save Results
            dataset_name = os.path.splitext(os.path.basename(dataset_path))[0]
            date_str = datetime.datetime.now().strftime("%Y-%m-%d")

            # Sanitize model name for filename
            safe_model_name = model_name.replace("/", "_")

            # Add scenario to filename if present
            scenario_part = f"_{scenario}" if scenario else ""

            base_filename = f"results_{date_str}_{dataset_name}_{provider}_{safe_model_name}{scenario_part}_{defense_name}"
            csv_file = os.path.join(output_dir, f"{base_filename}.csv")
            md_file = os.path.join(output_dir, f"{base_filename}.md")

            runner.save_results(csv_file)
            runner.save_summary(md_file)
            runner.print_summary()

    logger.end_execution()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Prompt Injection Benchmark")
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/attack_dataset.json",
        help="Path to dataset file",
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        default=["gemini:gemini-2.5-flash-lite"],
        help="List of models in format provider:model_name (e.g. gemini:gemini-2.5-flash-lite openai:gpt-3.5-turbo)",
    )
    parser.add_argument(
        "--defenses",
        type=str,
        nargs="+",
        default=["all"],
        help="List of defenses to run (no_defense, sandwich, instructional, xml_tagging, signed_prompt, all)",
    )
    parser.add_argument(
        "--output", type=str, default="results", help="Output directory"
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Limit the number of test cases to run"
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Disable LLM response caching"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode (prints system prompts)"
    )

    parser.add_argument(
        "--use-laaj", action="store_true", help="Enable LLM as a Judge evaluation"
    )

    parser.add_argument(
        "--scenario",
        type=str,
        default=None,
        help="Filter test cases by scenario (e.g. Banking, Ecommerce)",
    )

    args = parser.parse_args()

    run_benchmark(
        args.dataset,
        args.models,
        args.defenses,
        args.output,
        args.limit,
        not args.no_cache,
        args.debug,
        args.use_laaj,
        args.scenario,
    )
