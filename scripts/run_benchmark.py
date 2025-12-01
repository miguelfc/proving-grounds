#!/usr/bin/env python3
"""
Benchmark Script
Runs the prompt injection benchmark across multiple models and defenses.
"""
import argparse
import os
import sys
import time
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

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
)

def get_defenses(defense_names: List[str]):
    defenses = []
    if "all" in defense_names or "no_defense" in defense_names:
        defenses.append(NoDefense())
    if "all" in defense_names or "sandwich" in defense_names:
        defenses.append(SandwichDefense())
    if "all" in defense_names or "instructional" in defense_names:
        defenses.append(InstructionalDefense())
    if "all" in defense_names or "xml_tagging" in defense_names:
        defenses.append(XMLTaggingDefense())
    if "all" in defense_names or "signed_prompt" in defense_names:
        defenses.append(SignedPromptDefense())
    
    return defenses

def run_benchmark(dataset_path: str, models: List[str], defense_names: List[str], output_dir: str, limit: int = None, use_cache: bool = True, debug: bool = False):
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
            print("Warning: data/dataset_config/rate_limits.yaml not found. Proceeding without rate limits.")
        
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
            client = create_client(provider, model_name, use_cache=use_cache, rpm_limit=rpm_limit)
        except Exception as e:
            print(f"Failed to initialize client for {model_name}: {e}")
            continue

        evaluator = Evaluator()
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
                result_file = os.path.join(output_dir, f"results_{provider}_{model_name}_{defense_name}_PARTIAL.csv")
                runner.save_results(result_file)
                
                sys.exit(1)
            
            # Save Results
            result_file = os.path.join(output_dir, f"results_{provider}_{model_name}_{defense_name}.csv")
            runner.save_results(result_file)
            runner.print_summary()

    logger.end_execution()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Prompt Injection Benchmark")
    parser.add_argument("--dataset", type=str, default="data/generated_dataset.json", help="Path to dataset file")
    parser.add_argument("--models", type=str, nargs="+", default=["gemini:gemini-2.5-flash-lite"], 
                        help="List of models in format provider:model_name (e.g. gemini:gemini-2.5-flash-lite openai:gpt-3.5-turbo)")
    parser.add_argument("--defenses", type=str, nargs="+", default=["all"], 
                        help="List of defenses to run (no_defense, sandwich, instructional, xml_tagging, signed_prompt, all)")
    parser.add_argument("--output", type=str, default="results", help="Output directory")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of test cases to run")
    parser.add_argument("--no-cache", action="store_true", help="Disable LLM response caching")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (prints system prompts)")
    
    args = parser.parse_args()
    
    run_benchmark(args.dataset, args.models, args.defenses, args.output, args.limit, not args.no_cache, args.debug)
