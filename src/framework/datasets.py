from dataclasses import dataclass
from typing import List, Iterator


@dataclass
class TestCase:
    id: str
    prompt: str
    is_attack: bool
    expected_behavior: str = ""
    injection_type: str = "DIRECT"  # "DIRECT" or "INDIRECT"
    scenario: str = "Banking"  # "Banking" or "Ecommerce"
    system_prompt_modifier: dict = (
        None  # {"mode": "append"/"overwrite", "content": "..."}
    )
    env_config: dict = (
        None  # Configuration for the environment (e.g., malicious emails)
    )
    eval_criteria: dict = None


class Dataset:
    """
    Base class for datasets.
    """

    def __init__(self):
        self.test_cases: List[TestCase] = []

    def __iter__(self) -> Iterator[TestCase]:
        return iter(self.test_cases)

    def __len__(self) -> int:
        return len(self.test_cases)

    def __add__(self, other: "Dataset") -> "Dataset":
        if not isinstance(other, Dataset):
            raise TypeError(
                f"unsupported operand type(s) for +: '{type(self).__name__}' and '{type(other).__name__}'"
            )
        new_dataset.test_cases = self.test_cases + other.test_cases
        return new_dataset

    def filter_by_scenario(self, scenario: str):
        """
        Filters the dataset to only include test cases for the given scenario.
        Case-insensitive match.
        """
        if not scenario:
            return

        scenario = scenario.lower()
        self.test_cases = [
            case for case in self.test_cases if case.scenario.lower() == scenario
        ]
        print(
            f"Filtered dataset to scenario '{scenario}'. Remaining cases: {len(self.test_cases)}"
        )


class FileDataset(Dataset):
    """
    Dataset loaded from a CSV file.
    Expected CSV format: id,prompt,is_attack,expected_behavior
    """

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self._load_from_file()

    def _load_from_file(self):
        import csv
        import os

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Dataset file not found: {self.file_path}")

        with open(self.file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic validation
                if "prompt" not in row:
                    continue

                is_attack = row.get("is_attack", "false").lower() == "true"

                self.test_cases.append(
                    TestCase(
                        id=row.get("id", f"CASE_{len(self.test_cases)}"),
                        prompt=row["prompt"],
                        is_attack=is_attack,
                        expected_behavior=row.get("expected_behavior", ""),
                    )
                )


class JSONDataset(Dataset):
    """
    Dataset loaded from a JSON file.
    Supports flexible test case format with scenario selection,
    system prompt modification, and environment configuration.
    """

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path
        self._load_from_file()

    def _load_from_file(self):
        import json
        import os

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Dataset file not found: {self.file_path}")

        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Support both array and object format
        if isinstance(data, dict) and "test_cases" in data:
            test_cases_data = data["test_cases"]
        elif isinstance(data, list):
            test_cases_data = data
        else:
            raise ValueError("JSON must be an array or object with 'test_cases' key")

        for item in test_cases_data:
            # Parse env_config for indirect attacks
            env_config = None
            if "env_config" in item:
                env_config = self._parse_env_config(item["env_config"])

            self.test_cases.append(
                TestCase(
                    id=item.get("id", f"CASE_{len(self.test_cases)}"),
                    prompt=item["prompt"],
                    is_attack=item.get("is_attack", False),
                    expected_behavior=item.get("expected_behavior", ""),
                    injection_type=item.get("injection_type", "DIRECT"),
                    scenario=item.get("scenario", "Banking"),
                    system_prompt_modifier=item.get("system_prompt_modifier"),
                    env_config=env_config,
                    eval_criteria=item.get("eval_criteria"),
                )
            )

    def _parse_env_config(self, config: dict) -> dict:
        """Parse environment configuration, converting dicts to proper objects."""
        from src.framework.environments import Email

        parsed = {}

        # Parse inbox emails
        if "inbox" in config:
            parsed["inbox"] = []
            for i, email_data in enumerate(config["inbox"]):
                if isinstance(email_data, dict):
                    parsed["inbox"].append(
                        Email(
                            id=email_data.get("id", f"email_{i}"),
                            sender=email_data.get("sender", "unknown@example.com"),
                            recipient=email_data.get("recipient", "user@example.com"),
                            subject=email_data.get("subject", ""),
                            body=email_data.get("body", ""),
                        )
                    )
                else:
                    parsed["inbox"].append(email_data)

        # Parse inventory products
        if "inventory" in config:
            parsed["inventory"] = {}
            for product_id, product_data in config["inventory"].items():
                # Pass product data as dict, as expected by EcommerceEnvironment
                parsed["inventory"][product_id] = product_data

        # Pass through other config as-is
        for key, value in config.items():
            if key not in ["inbox", "inventory"]:
                parsed[key] = value

        return parsed
