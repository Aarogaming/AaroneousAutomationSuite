from typing import Optional, Any
from langchain_ollama import ChatOllama
from loguru import logger
from core.config.manager import AASConfig

class OllamaClient:
    """
    Local LLM Integration via Ollama.
    Provides a fallback or primary LLM for privacy-sensitive tasks.
    """
    def __init__(self, config: AASConfig):
        self.config = config
        self.base_url = config.ollama_url
        self.model = "llama3" # Default model
        
    def get_model(self, model_name: Optional[str] = None) -> ChatOllama:
        """Returns a ChatOllama instance."""
        m = model_name or self.model
        logger.info(f"Initializing local LLM: {m} at {self.base_url}")
        return ChatOllama(
            model=m,
            base_url=self.base_url,
            temperature=0
        )

    def generate(self, prompt: str, model_name: Optional[str] = None) -> str:
        """Simple generation wrapper."""
        try:
            llm = self.get_model(model_name)
            response = llm.invoke(prompt)
            return str(response.content)
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return f"Error: {e}"
