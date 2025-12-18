import os
import csv
import glob
from pathlib import Path

# Constants
RESULTS_DIR = Path("results")
OUTPUT_MD_NAME = "consolidated_results.md"
OUTPUT_BRIEF_MD_NAME = "consolidated_results_brief.md"
OUTPUT_CSV_NAME = "consolidated_results.csv"
PROVIDERS = ["openai", "gemini", "claude", "huggingface"]
SCENARIOS = ["Ecommerce", "Banking"]


def parse_filename(filename):
    """
    Parses the filename to extract:
    Date, Dataset, Model, Scenario, Defense.

    Filename format:
    results_{date}_{dataset_str}_{provider}_{model_str}_{scenario}_{defense}.(md|csv)
    or
    results_{date}_{dataset_str}_{provider}_{model_str}_{defense}.(md|csv) (No scenario)

    Assumption:
    - Prefix is 'results_'
    - Date is YYYY-MM-DD
    - Dataset and Model are separated by the provider keyword.
    - Defense is the last part.
    - Scenario is the second to last part IF it is a known scenario.
    """
    name = filename.stem  # filename without extension
    if not name.startswith("results_"):
        return None

    # Remove 'results_' prefix
    core_name = name[8:]

    # Split by '_'
    parts = core_name.split("_")

    if len(parts) < 4:
        # Unexpected format, not enough parts
        return None

    date = parts[0]

    # Extract Defense (last part)
    defense = parts[-1]

    # Check for Scenario
    scenario = None
    remaining_parts = parts[1:-1]  # Parts between date and defense

    if remaining_parts and remaining_parts[-1] in SCENARIOS:
        scenario = remaining_parts[-1]
        remaining_parts = remaining_parts[:-1]

    # Now remaining_parts contains Dataset + Provider + Model
    # Find provider index to split Dataset and Model
    provider_idx = -1
    for i, part in enumerate(remaining_parts):
        if part in PROVIDERS:
            provider_idx = i
            break

    if provider_idx != -1:
        dataset = "_".join(remaining_parts[:provider_idx])
        model = "_".join(remaining_parts[provider_idx:])
    else:
        # Fallback: if provider not found, this logic might fail.
        # We'll try to guess. 'combined_dataset' is common.
        if (
            len(remaining_parts) >= 2
            and remaining_parts[0] == "combined"
            and remaining_parts[1] == "dataset"
        ):
            dataset = "combined_dataset"
            model = "_".join(remaining_parts[2:])
        else:
            # Last resort: unknown split.
            dataset = "unknown"
            model = "_".join(remaining_parts)

    return {
        "Date": date,
        "Dataset": dataset,
        "Model": model,
        "Scenario": scenario if scenario else "N/A",
        "Defense": defense,
    }


def consolidate_md_files(md_files, output_path, brief=False):
    action = "Briefly consolidating" if brief else "Consolidating"
    print(f"{action} {len(md_files)} MD files to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.write("# Consolidated Results\n\n")

        for file_path in sorted(md_files):
            # Skip the output files themselves if they exist in the list
            if file_path.name in [OUTPUT_MD_NAME, OUTPUT_BRIEF_MD_NAME]:
                continue

            metadata = parse_filename(file_path)
            if not metadata:
                print(f"Skipping file with invalid name format: {file_path}")
                continue

            # Create Header
            header = (
                f"\n---\n"
                f"# File: {file_path.name}\n"
                f"**Date**: {metadata['Date']} | "
                f"**Dataset**: {metadata['Dataset']} | "
                f"**Model**: {metadata['Model']} | "
                f"**Scenario**: {metadata['Scenario']} | "
                f"**Defense**: {metadata['Defense']}\n"
                f"---\n\n"
            )
            outfile.write(header)

            with open(file_path, "r", encoding="utf-8") as infile:
                content = infile.read()
                if brief:
                    # Cut off at "## Detailed Results"
                    split_marker = "## Detailed Results"
                    if split_marker in content:
                        content = content.split(split_marker)[0]
                    else:
                        # If the marker isn't found, keep content as is?
                        # Or maybe try standardizing newline before checking?
                        # Let's hope the marker is consistent.
                        pass
                outfile.write(content)
                outfile.write("\n\n")


def consolidate_csv_files(csv_files, output_path):
    print(f"Consolidating {len(csv_files)} CSV files to {output_path}...")

    all_rows = []
    fieldnames = set()

    # Fixed columns to come first
    metadata_cols = ["Date", "Dataset", "Model", "Scenario", "Defense"]

    for file_path in sorted(csv_files):
        if file_path.name == OUTPUT_CSV_NAME:
            continue

        metadata = parse_filename(file_path)
        if not metadata:
            print(f"Skipping file with invalid name format: {file_path}")
            continue

        with open(file_path, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            if reader.fieldnames:
                fieldnames.update(reader.fieldnames)

            for row in reader:
                # Add metadata columns
                full_row = row.copy()
                full_row.update(metadata)
                all_rows.append(full_row)

    if not all_rows:
        print("No CSV data found.")
        return

    # Prepare final fieldnames order
    final_fieldnames = metadata_cols + [
        f for f in sorted(list(fieldnames)) if f not in metadata_cols
    ]

    with open(output_path, "w", encoding="utf-8", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=final_fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)


def main():
    # Find all files recursively in RESULTS_DIR
    all_md_files = list(RESULTS_DIR.rglob("*.md"))
    all_csv_files = list(RESULTS_DIR.rglob("*.csv"))

    # Filter out the output files if they are picked up (e.g. if script is run multiple times)
    # Also exclude Execution Log
    all_md_files = [
        f
        for f in all_md_files
        if f.name not in [OUTPUT_MD_NAME, OUTPUT_BRIEF_MD_NAME, "Execution Log.md"]
    ]
    all_csv_files = [f for f in all_csv_files if f.name != OUTPUT_CSV_NAME]

    consolidate_md_files(all_md_files, RESULTS_DIR / OUTPUT_MD_NAME, brief=False)
    consolidate_md_files(all_md_files, RESULTS_DIR / OUTPUT_BRIEF_MD_NAME, brief=True)
    consolidate_csv_files(all_csv_files, RESULTS_DIR / OUTPUT_CSV_NAME)

    print("Consolidation complete.")


if __name__ == "__main__":
    main()
