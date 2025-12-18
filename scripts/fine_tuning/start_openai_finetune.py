#!/usr/bin/env python3
"""
Script to upload training data and start an OpenAI fine-tuning job.

Usage:
    python scripts/start_finetune.py --file jatmo_train.jsonl --model gpt-4.1-mini-2025-04-14
"""

import argparse
import os
import sys
import time
from openai import OpenAI, OpenAIError

# Load environment variables if not already loaded (e.g. via dotenv)
from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Start an OpenAI Fine-Tuning Job")
    parser.add_argument(
        "--file", type=str, required=True, help="Path to the training data JSONL file"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4.1-mini-2025-04-14",
        help="Base model to fine-tune (default: gpt-4.1-mini-2025-04-14)",
    )
    parser.add_argument(
        "--suffix",
        type=str,
        default=None,
        help="Optional suffix for the fine-tuned model name",
    )

    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not found.")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # 1. Upload File
    print(f"Uploading {args.file}...")
    try:
        with open(args.file, "rb") as f:
            response = client.files.create(file=f, purpose="fine-tune")
        file_id = response.id
        print(f"✅ File uploaded successfully. ID: {file_id}")
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)
    except OpenAIError as e:
        print(f"Error uploading file: {e}")
        sys.exit(1)

    # 2. Wait for file processing (usually instant for small files, but good practice)
    print("Waiting for file to be ready...")
    while True:
        try:
            file_info = client.files.retrieve(file_id)
            if file_info.status == "processed":
                break
            elif file_info.status == "error":
                print("Error: File processing failed.")
                sys.exit(1)
            time.sleep(1)
        except OpenAIError as e:
            print(f"Error checking file status: {e}")
            time.sleep(2)

    # 3. Start Fine-Tuning Job
    print(f"Starting fine-tuning job for base model '{args.model}'...")
    try:
        job_params = {"training_file": file_id, "model": args.model}
        if args.suffix:
            job_params["suffix"] = args.suffix

        job = client.fine_tuning.jobs.create(**job_params)

        job_id = job.id
        print(f"✅ Fine-tuning job started successfully.")
        print(f"Job ID: {job_id}")
        print(
            f"Model will be named: {job.fine_tuned_model} (initially null until complete)"
        )
        print(f"\nTo monitor status, run:")
        print(f"  openai api fine_tuning.jobs.retrieve -i {job_id}")
        print(f"Or check the OpenAI Dashboard.")
        print(f"\nOnce complete, use the 'fine_tuned_model' ID with the Jatmo defense:")
        print(f"  python scripts/run_benchmark.py --defenses jatmo:<NEW_MODEL_ID> ...")

    except OpenAIError as e:
        print(f"Error starting fine-tuning job: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
