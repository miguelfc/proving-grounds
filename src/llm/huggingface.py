from src.llm.base import LLMClient

class LocalHuggingFaceClient(LLMClient):
    """
    Implementation for local open-source models (e.g., Llama-3, Mistral).
    Crucial for 'Perplexity-Based Detection' where access to raw logits/tokens is needed.
    """
    def __init__(self, model_path: str, device: str = "cpu"):
        # We import here to avoid loading heavy libraries if not used
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        
        print(f"Loading local model: {model_path}...")
        self.device = "cuda" if torch.cuda.is_available() and device == "cuda" else "cpu"
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(model_path).to(self.device)
        self.model_name = model_path
        print("Model loaded.")

    def generate_response(self, system_prompt: str, user_input: str, temperature: float = 0.7) -> str:
        import torch
        
        # Constructing the prompt manually (simplistic template)
        # Note: Different models (Llama, Mistral) have specific chat templates.
        full_prompt = f"System: {system_prompt}\nUser: {user_input}\nAssistant:"
        
        inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs, 
                max_new_tokens=150, 
                temperature=temperature,
                do_sample=True if temperature > 0 else False
            )
            
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Simple parsing to remove the prompt from the output
        return response.replace(full_prompt, "").strip()
