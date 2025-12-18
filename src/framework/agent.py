import re
import time
from typing import List, Dict, Any, Optional, Tuple
from src.llm import LLMClient
from src.framework.environments.base.environment import Environment


class Agent:
    """
    Wraps an LLMClient and manages the interaction with the environment.
    """

    def __init__(self, client: LLMClient, tools: Any, system_prompt: str = None):
        self.client = client
        self.tools = tools

        # Determine base prompt
        base_prompt = system_prompt
        if base_prompt is None:
            if hasattr(self.tools, "get_default_system_prompt"):
                base_prompt = self.tools.get_default_system_prompt()
            else:
                base_prompt = "You are a helpful Assistant."

        self.system_prompt = self._construct_full_prompt(base_prompt)
        self.chat_history = []

    def _construct_full_prompt(self, base_prompt: str) -> str:
        return f"""{base_prompt}

You have access to the following tools:
{self.tools.get_tool_definitions()}

To use a tool, output the function call in the format: `TOOL_CALL: function_name(arguments)`
Example: `TOOL_CALL: check_balance(account_id='user_main')`

If you don't need to use a tool, just answer the user directly.
"""

    def step(self, observation: str) -> Tuple[str, float]:
        """
        Takes an observation (user input or tool output), generates a response.
        Returns: (response_text, latency)
        """
        # Append observation to history
        # Note: The Pipeline handles appending the 'User' message to history before calling step?
        # No, let's have the Agent manage its internal view of the prompt.

        # Construct the full prompt including history
        # Since LLMClient.generate_response takes (system, user_input),
        # we will pack the entire history into 'user_input'.

        full_conversation = ""
        for msg in self.chat_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            full_conversation += f"{role}: {msg['content']}\n"

        full_conversation += f"User: {observation}\nAssistant:"

        # Call LLM
        start_time = time.time()
        response = self.client.generate_response(self.system_prompt, full_conversation)
        duration = time.time() - start_time

        # Use stored latency if available (e.g. from cache)
        if (
            hasattr(self.client, "last_latency")
            and self.client.last_latency is not None
        ):
            duration = self.client.last_latency

        return response, duration


class Pipeline:
    """
    Manages the simulation loop: Agent -> Tool -> Environment -> Agent
    """

    def __init__(self, environment: Environment, agent: Agent):
        self.env = environment
        self.agent = agent
        self.max_steps = 5

    def run(self, initial_instruction: str) -> Dict[str, Any]:
        """
        Runs the simulation loop.
        """
        print(f"--- Starting Pipeline Run ---")
        print(f"Instruction: {initial_instruction}")

        current_input = initial_instruction
        # Reset agent history for this run
        self.agent.chat_history = []

        for step in range(self.max_steps):
            print(f"\n[Step {step+1}]")

            # 1. Agent Step
            response, latency = self.agent.step(current_input)
            print(f"Agent: {response}")

            # 2. Tool Execution Logic (Parse BEFORE appending to history)
            tool_call = self._parse_tool_call(response)

            # Prepare assistant message entry
            assistant_msg = {
                "role": "assistant",
                "content": response,
                "latency": latency,
            }

            if tool_call:
                print(f"  -> Tool Call Detected: {tool_call['name']}")

                # Add structured tool call info to history for Evaluator
                assistant_msg["tool_calls"] = [
                    {
                        "function": {
                            "name": tool_call["name"],
                            "arguments": str(
                                tool_call["args"]
                            ),  # Store as string representation as per convention
                        }
                    }
                ]

            # Update history with structured info (Always update history)
            self.agent.chat_history.append({"role": "user", "content": current_input})
            self.agent.chat_history.append(assistant_msg)

            if tool_call:
                # Execute Tool
                tool_output = self.agent.tools.execute(
                    tool_call["name"], tool_call["args"]
                )
                print(f'  -> Tool Output: "{tool_output}"')

                # 3. Update Input for next step
                current_input = f'Tool Output: "{tool_output}"'

                # Check if we should stop (e.g., if the tool output indicates success or failure)
                # For now, we continue to let the agent react to the tool output.
            else:
                # No tool call, agent just replied.
                print("  -> No tool call. Ending turn.")
                break

        return {"history": self.agent.chat_history, "final_state": self.env.get_state()}

    def _parse_tool_call(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parses the LLM response for tool calls.
        Supports `TOOL_CALL: name(args)` and markdown blocks.
        """
        cmd_str = None
        if "TOOL_CALL:" in response:
            cmd_str = response.split("TOOL_CALL:")[1].strip()
        elif "```tool_call" in response:
            parts = response.split("```tool_call")
            if len(parts) > 1:
                cmd_str = parts[1].split("```")[0].strip()

        if cmd_str:
            # Clean up
            cmd_str = cmd_str.split("\n")[0]

            # Parse name and args
            # Regex to capture name and content inside parentheses
            match = re.match(r"(\w+)\((.*)\)", cmd_str)
            if match:
                name = match.group(1)
                args_str = match.group(2)

                # Parse args safely
                # We'll use eval with a safe scope to parse the arguments string into a dict or list
                # This handles 'a=1, b="foo"' style if we wrap it in a dict, or just positional.
                # Actually, our tools use kwargs. Let's try to parse it as python kwargs.
                # Hacky but works for prototype: eval(f"dict({args_str})")
                try:
                    # Try parsing as kwargs first
                    args = eval(f"dict({args_str})")
                    return {"name": name, "args": args}
                except Exception:
                    # Fallback: maybe it's just positional args?
                    # But our tools expect kwargs.
                    # Let's try to be robust.
                    print(f"Warning: Could not parse args as dict: {args_str}")
                    return None
        return None
