class LLMProvider:
    def __init__(self, *args, **kwargs):
        self.use_local = False
    def generate(self, *args, **kwargs):
        return "Mock response"
    def chat(self, *args, **kwargs):
        return {"content": "Mock response", "model": "mock"}

class OllamaClient:
    def __init__(self, *args, **kwargs):
        self.base_url = "http://localhost:11434"
    def is_available(self):
        return False
    def list_models(self):
        return []
    def generate(self, *args, **kwargs):
        return {"response": "Mock response"}
