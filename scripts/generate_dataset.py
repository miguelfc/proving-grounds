import yaml
import json
import os
import sys
import uuid
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.framework.environments import Email

# Configuration Paths
CONFIG_DIR = "data/dataset_config"
USER_TASKS_FILE = os.path.join(CONFIG_DIR, "user_tasks.yaml")
ATTACKER_GOALS_FILE = os.path.join(CONFIG_DIR, "attacker_goals.yaml")
ATTACK_METHODS_FILE = os.path.join(CONFIG_DIR, "attack_methods.yaml")
INJECTION_LOCATIONS_FILE = os.path.join(CONFIG_DIR, "injection_locations.yaml")

OUTPUT_FILE = "data/generated_dataset.json"

def load_yaml(filepath: str) -> List[Dict]:
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)

def generate_dataset():
    print("Loading configurations...")
    user_tasks = load_yaml(USER_TASKS_FILE)
    attacker_goals = load_yaml(ATTACKER_GOALS_FILE)
    attack_methods = load_yaml(ATTACK_METHODS_FILE)
    injection_locations = load_yaml(INJECTION_LOCATIONS_FILE)

    test_cases = []

    print("Generating test cases...")
    
    for task in user_tasks:
        scenario = task["scenario"]
        compatible_locations = task.get("compatible_locations", [])
        
        for location_id in compatible_locations:
            # Find the location definition
            location = next((l for l in injection_locations if l["id"] == location_id), None)
            if not location:
                print(f"Warning: Location '{location_id}' not found for task '{task['id']}'")
                continue
            
            # Check scenario match
            if location["scenario"] != scenario:
                continue

            for goal in attacker_goals:
                # Filter compatible methods
                compatible_methods_ids = goal.get("compatible_methods", [])
                
                for method in attack_methods:
                    # Skip if method is not compatible (if compatibility list is present)
                    if compatible_methods_ids and method["id"] not in compatible_methods_ids:
                        continue
                        
                    # 1. Check Context
                    method_context = method.get("context", {})
                    goal_text = goal["goal"]
                    
                    try:
                        rendered_goal = goal_text.format(**method_context)
                    except KeyError:
                        # Method doesn't provide necessary context for this goal
                        continue
                    except ValueError:
                        print(f"Warning: Malformed format string in goal {goal['id']}")
                        continue

                    # 2. Generate Attack String
                    combined_context = method_context.copy()
                    combined_context["goal"] = rendered_goal
                    
                    # --- Special Handling for Base64 ---
                    import base64
                    
                    # Generate Base64 version of the goal
                    combined_context["goal_base64"] = base64.b64encode(rendered_goal.encode('utf-8')).decode('utf-8')
                    
                    try:
                        attack_string = method["template"].format(**combined_context)
                    except KeyError as e:
                        # print(f"Skipping method {method['id']} for goal {goal['id']}: missing key {e}")
                        continue
                    
                    # 2. Inject into Location
                    injected_content = location["template"].replace("{attack}", attack_string)
                    
                    # 3. Create Environment Config & Prompt
                    env_config = {}
                    final_prompt = task["prompt"]
                    injection_type = "INDIRECT"
                    
                    if location["type"] == "email":
                        # Create a malicious email
                        email_data = {
                            "id": str(uuid.uuid4())[:8],
                            "sender": "attacker@external.com",
                            "recipient": "user@internal.com",
                            "subject": "Important Update", # Could also be templated
                            "body": injected_content
                        }
                        env_config["inbox"] = [email_data]
                        
                    elif location["type"] == "file":
                        # Create a malicious file
                        env_config["files"] = {
                            location["filename"]: injected_content
                        }

                    elif location["type"] == "direct":
                        # Direct Injection: The prompt IS the attack (or contains it)
                        # For now, we'll just replace the prompt with the attack string
                        # In a more complex setup, we might append it to the benign prompt
                        final_prompt = injected_content
                        injection_type = "DIRECT"
                    
                    # 4. Create Test Case
                    case_id = f"{task['id']}_{location['id']}_{goal['id']}_{method['id']}"
                    
                    test_case = {
                        "id": case_id,
                        "prompt": final_prompt,
                        "is_attack": True,
                        "expected_behavior": goal["expected_behavior"],
                        "injection_type": injection_type,
                        "scenario": scenario,
                        "env_config": env_config,
                        "metadata": {
                            "user_task": task["id"],
                            "attacker_goal": goal["id"],
                            "attack_method": method["id"],
                            "injection_location": location["id"]
                        }
                    }
                    
                    test_cases.append(test_case)

    print(f"Generated {len(test_cases)} test cases.")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(test_cases, f, indent=2)
    
    print(f"Dataset saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_dataset()
