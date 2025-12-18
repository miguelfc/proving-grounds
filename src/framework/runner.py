import time
import csv
from typing import List, Type, Dict, Any
from src.llm import LLMClient
from src.framework.defenses import DefenseStrategy
from src.framework.datasets import Dataset, TestCase
from src.framework.evaluator import Evaluator, EvaluationResult
from src.framework.logger import logger


class TestRunner:
    """
    Orchestrates the benchmarking process.
    """

    def __init__(self, llm_client: LLMClient, evaluator: Evaluator):
        self.llm_client = llm_client
        self.evaluator = evaluator
        self.results: List[Dict[str, Any]] = []

    def run(
        self,
        dataset: Dataset,
        defense: DefenseStrategy,
        system_prompt: str = None,
        limit: int = None,
        debug: bool = False,
    ):
        """
        Runs the benchmark on a given dataset with a specific defense.

        Args:
            dataset: The dataset to run (Malicious or Legitimate).
            defense: The defense strategy to apply.
            system_prompt: The base system prompt to use.
            limit: Optional limit on the number of API calls (cache misses).
        """
        logger.log(
            f"Starting run with defense: {defense.__class__.__name__} on {len(dataset)} cases."
        )

        for i, case in enumerate(dataset):
            # Check limit before running
            if limit is not None and i >= limit:
                logger.log(f"Limit of {limit} test cases reached. Stopping.")
                break

            self._run_single_case(case, defense, system_prompt, debug)

        logger.log("Run completed.")

    def _run_single_case(
        self,
        case: TestCase,
        defense: DefenseStrategy,
        system_prompt: str = None,
        debug: bool = False,
    ):
        from src.framework.environments.banking.environment import BankingEnvironment
        from src.framework.environments.ecommerce.environment import (
            EcommerceEnvironment,
        )
        from src.framework.environments.banking.tools import BankingTools
        from src.framework.environments.ecommerce.tools import EcommerceTools
        from src.framework.agent import Agent, Pipeline

        # 1. Setup Environment based on scenario
        if case.scenario == "Ecommerce":
            env = EcommerceEnvironment()
            tools = EcommerceTools(env)
        else:  # Default to Banking
            env = BankingEnvironment()
            tools = BankingTools(env)

        # Apply env_config if provided
        if case.env_config:
            if "inbox" in case.env_config:
                for email in case.env_config["inbox"]:
                    env.add_email(email)
            if "inventory" in case.env_config:
                for product_id, product in case.env_config["inventory"].items():
                    if hasattr(env, "inventory"):
                        env.inventory[product_id] = product

            # Support for new internal service simulations
            if "files" in case.env_config and hasattr(env, "files"):
                env.files.update(case.env_config["files"])
            if "users" in case.env_config and hasattr(env, "users"):
                env.users.update(case.env_config["users"])
            if "suppliers" in case.env_config and hasattr(env, "suppliers"):
                env.suppliers.update(case.env_config["suppliers"])

        # 1.5. Apply system prompt modifications
        if system_prompt:
            final_system_prompt = system_prompt
        else:
            final_system_prompt = tools.get_default_system_prompt()

        if case.system_prompt_modifier:
            mode = case.system_prompt_modifier.get("mode", "append")
            content = case.system_prompt_modifier.get("content", "")

            if mode == "overwrite":
                final_system_prompt = content
            elif mode == "append":
                final_system_prompt = system_prompt + "\n" + content

        # 2. Apply Defense
        protected_system_prompt, protected_user_prompt = defense.apply(
            final_system_prompt, case.prompt
        )

        # 2.5. Check for Model Override (Jatmo Defense)
        original_model = None
        if hasattr(defense, "get_model_override"):
            model_override = defense.get_model_override()
            if model_override:
                original_model = getattr(self.llm_client, "model_name", None)
                logger.log(
                    f"  [Model Override] Switching from {original_model} to {model_override}"
                )
                # Handle both direct clients and cached clients
                if hasattr(self.llm_client, "client"):
                    # CachedLLMClient - update wrapped client
                    self.llm_client.client.model_name = model_override
                    self.llm_client.model_name = model_override
                else:
                    # Direct client
                    self.llm_client.model_name = model_override

        # 3. Initialize Agent & Pipeline
        agent = Agent(self.llm_client, tools, system_prompt=protected_system_prompt)
        pipeline = Pipeline(env, agent)

        if debug:
            logger.log(f"DEBUG: System Prompt:\n{agent.system_prompt}\n")
            logger.log(f"DEBUG: User Prompt:\n{protected_user_prompt}\n")

        # 4. Run Pipeline
        start_time = time.time()
        pipeline_result = pipeline.run(initial_instruction=protected_user_prompt)

        # 4.5. Restore Original Model (if overridden)
        if original_model:
            logger.log(f"  [Model Restore] Switching back to {original_model}")
            if hasattr(self.llm_client, "client"):
                self.llm_client.client.model_name = original_model
                self.llm_client.model_name = original_model
            else:
                self.llm_client.model_name = original_model

        # 5. Evaluate
        # We extract the final response from the history
        final_response = ""
        if pipeline_result["history"]:
            final_response = pipeline_result["history"][-1]["content"]

        result: EvaluationResult = self.evaluator.evaluate(
            pipeline_result=pipeline_result,
            expected_behavior=case.expected_behavior,
            is_attack=case.is_attack,
            start_time=start_time,
            eval_criteria=getattr(case, "eval_criteria", {}),
        )

        # 6. Log Result
        if case.is_attack:
            log_status = (
                "ATTACK SUCCEEDED (BAD)"
                if result.logical_success
                else "ATTACK BLOCKED (GOOD)"
            )
        else:
            log_status = (
                "QUERY ANSWERED (GOOD)"
                if result.logical_success
                else "QUERY BLOCKED (BAD)"
            )

        logger.log(
            f"ID: {case.id} | Type: {getattr(case, 'injection_type', 'DIRECT')} | {log_status}"
        )
        if result.logical_success and case.is_attack:
            logger.log(f"  -> ATTACK SUCCEEDED! Response: {final_response[:100]}...")

        self.results.append(
            {
                "id": case.id,
                "is_attack": case.is_attack,
                "logical_success": result.logical_success,
                "logical_detection_method": result.logical_detection_method,
                "laaj_success": result.laaj_success,
                "laaj_reasoning": result.laaj_reasoning,
                "latency": result.latency,
                "laaj_latency": result.laaj_latency,
                "response": result.response,
                "defense": defense.__class__.__name__,
                "type": getattr(case, "injection_type", "DIRECT"),
                "scenario": case.scenario,
                "cache_hash": getattr(self.llm_client, "last_cache_key", ""),
            }
        )

    def save_results(self, filename: str):
        if not self.results:
            logger.log("No results to save.")
            return

        # Define columns based on user request
        fieldnames = [
            "id",
            "cache_hash",
            "logical_result",
            "logical_detection_method",
            "laaj_result",
            "laaj_reasoning",
            "is_attack",
            "type",
            "scenario",
            "defense",
            "response",
            "latency",
            "laaj_latency",
        ]

        with open(filename, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for r in self.results:
                is_attack = r["is_attack"]
                logical_success = r["logical_success"]
                laaj_success = r.get("laaj_success")

                # Logical Result
                if is_attack:
                    logical_outcome = "FAIL" if logical_success else "PASS"
                else:
                    logical_outcome = "PASS" if logical_success else "FAIL"

                # LaaJ Result
                laaj_outcome = "N/A"
                if laaj_success is not None:
                    if is_attack:
                        laaj_outcome = "FAIL" if laaj_success else "PASS"
                    else:
                        laaj_outcome = "PASS" if laaj_success else "FAIL"

                row = {
                    "id": r["id"],
                    "cache_hash": r.get("cache_hash", ""),
                    "logical_result": logical_outcome,
                    "logical_detection_method": r["logical_detection_method"],
                    "laaj_result": laaj_outcome,
                    "laaj_reasoning": r.get("laaj_reasoning", "N/A"),
                    "is_attack": is_attack,
                    "type": r.get("type", "DIRECT"),
                    "scenario": r.get("scenario", "Banking"),
                    "defense": r.get("defense", "None"),
                    "response": (
                        r["response"].replace("\n", "\\n").replace("\r", "")
                        if r["response"]
                        else ""
                    ),
                    "latency": f"{r['latency']:.4f}",
                    "laaj_latency": f"{r.get('laaj_latency', 0.0) or 0.0:.4f}",
                }
                writer.writerow(row)

        logger.log(f"Results saved to {filename}")

    def save_summary(self, filename: str):
        if not self.results:
            return

        total_attacks = len([r for r in self.results if r["is_attack"]])
        total_benign = len([r for r in self.results if not r["is_attack"]])

        successful_attacks = len(
            [r for r in self.results if r["is_attack"] and r["logical_success"]]
        )
        successful_benign = len(
            [r for r in self.results if not r["is_attack"] and r["logical_success"]]
        )

        asr = (successful_attacks / total_attacks * 100) if total_attacks > 0 else 0.0
        # False Positive Rate: Benign queries that FAILED (were blocked)
        fpr = (
            ((total_benign - successful_benign) / total_benign * 100)
            if total_benign > 0
            else 0.0
        )

        # LaaJ Metrics
        laaj_successful_attacks = len(
            [r for r in self.results if r["is_attack"] and r.get("laaj_success")]
        )
        laaj_successful_benign = len(
            [r for r in self.results if not r["is_attack"] and r.get("laaj_success")]
        )
        laaj_asr = (
            (laaj_successful_attacks / total_attacks * 100)
            if total_attacks > 0
            else 0.0
        )
        laaj_fpr = (
            ((total_benign - laaj_successful_benign) / total_benign * 100)
            if total_benign > 0
            else 0.0
        )

        with open(filename, "w") as f:
            f.write(f"# Benchmark Summary\n\n")
            f.write(f"- **Date**: {time.strftime('%Y-%m-%d')}\n")
            f.write(f"- **Total Cases**: {len(self.results)}\n")
            f.write(f"- **Total Attacks**: {total_attacks}\n")
            f.write(f"- **Total Benign**: {total_benign}\n\n")
            f.write(f"## Metrics\n")
            f.write(f"- **Logical Attack Success Rate (ASR)**: {asr:.2f}%\n")
            f.write(f"- **Logical False Positive Rate (FPR)**: {fpr:.2f}%\n")
            f.write(f"- **LaaJ Attack Success Rate (ASR)**: {laaj_asr:.2f}%\n")
            f.write(f"- **LaaJ False Positive Rate (FPR)**: {laaj_fpr:.2f}%\n\n")

            f.write(f"## Detailed Results\n")
            f.write(
                f"| ID | Type | Is Attack | Logical Result | LaaJ Result | Detection Method |\n"
            )
            f.write(f"|---|---|---|---|---|---|\n")

            for r in self.results:
                is_attack = r["is_attack"]
                logical_success = r["logical_success"]
                laaj_success = r.get("laaj_success")

                if is_attack:
                    log_res = "FAIL" if logical_success else "PASS"
                    laaj_res = (
                        "FAIL"
                        if list([laaj_success]) and laaj_success
                        else ("PASS" if laaj_success is False else "N/A")
                    )
                else:
                    log_res = "PASS" if logical_success else "FAIL"
                    laaj_res = (
                        "PASS"
                        if list([laaj_success]) and laaj_success
                        else ("FAIL" if laaj_success is False else "N/A")
                    )

                # Simplified LaaJ logic for display
                if laaj_success is None:
                    laaj_res = "N/A"
                elif is_attack:
                    laaj_res = "FAIL" if laaj_success else "PASS"
                else:
                    laaj_res = "PASS" if laaj_success else "FAIL"

                f.write(
                    f"| {r['id']} | {r['type']} | {str(is_attack)} | {log_res} | {laaj_res} | {r.get('logical_detection_method', 'Unknown')} |\n"
                )

        logger.log(f"Summary saved to {filename}")

    def print_summary(self):
        if not self.results:
            return

        total_attacks = len([r for r in self.results if r["is_attack"]])
        total_benign = len([r for r in self.results if not r["is_attack"]])

        successful_attacks = len(
            [r for r in self.results if r["is_attack"] and r["logical_success"]]
        )
        successful_benign = len(
            [r for r in self.results if not r["is_attack"] and r["logical_success"]]
        )

        asr = (successful_attacks / total_attacks * 100) if total_attacks > 0 else 0.0
        # False Positive Rate: Benign queries that FAILED (were blocked)
        fpr = (
            ((total_benign - successful_benign) / total_benign * 100)
            if total_benign > 0
            else 0.0
        )

        # LaaJ Metrics
        laaj_successful_attacks = len(
            [r for r in self.results if r["is_attack"] and r.get("laaj_success")]
        )
        laaj_successful_benign = len(
            [r for r in self.results if not r["is_attack"] and r.get("laaj_success")]
        )
        laaj_asr = (
            (laaj_successful_attacks / total_attacks * 100)
            if total_attacks > 0
            else 0.0
        )
        laaj_fpr = (
            ((total_benign - laaj_successful_benign) / total_benign * 100)
            if total_benign > 0
            else 0.0
        )

        logger.log("\n--- Benchmark Summary ---")
        logger.log(f"Total Attacks: {total_attacks}")
        logger.log(f"Logical ASR: {asr:.2f}%")
        logger.log(f"LaaJ ASR:    {laaj_asr:.2f}%")
        logger.log(f"Total Benign: {total_benign}")
        logger.log(f"Logical FPR: {fpr:.2f}%")
        logger.log(f"LaaJ FPR:    {laaj_fpr:.2f}%")
        logger.log("-------------------------")
