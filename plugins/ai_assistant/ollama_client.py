"""
Ollama Local LLM Client for AAS.

Provides a unified interface for interacting with locally-hosted LLMs via Ollama.
Supports fallback to OpenAI when local models are unavailable.
"""
import requests
from typing import Optional, Dict, Any, List
from loguru import logger
from core.config.manager import AASConfig


class OllamaClient:
    """
    Client for interacting with Ollama-hosted local LLMs.
    
    Supports streaming and non-streaming completions, model management,
    and health checking.
    """
    
    def __init__(self, config: AASConfig):
        """
        Initialize Ollama client.
        
        Args:
            config: AAS configuration with ollama_url
        """
        self.base_url = config.ollama_url or "http://localhost:11434"
        self.config = config
        self._available = None
        
    def is_available(self) -> bool:
        """
        Check if Ollama service is available.
        
        Returns:
            True if Ollama is running and accessible
        """
        if self._available is not None:
            return self._available
            
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            self._available = response.status_code == 200
            return self._available
        except requests.RequestException as e:
            logger.debug(f"Ollama not available: {e}")
            self._available = False
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models in Ollama.
        
        Returns:
            List of model information dicts
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            return response.json().get("models", [])
        except requests.RequestException as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []
    
    def generate(
        self,
        prompt: str,
        model: str = "llama2",
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Generate completion from Ollama model.
        
        Args:
            prompt: The prompt to send to the model
            model: Model name (default: llama2)
            system: Optional system prompt
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Response dict with 'response' and 'model' keys
            
        Raises:
            requests.RequestException: If API call fails
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
            
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            if stream:
                return {"stream": response.iter_lines(), "model": model}
            else:
                return response.json()
                
        except requests.RequestException as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama2",
        temperature: float = 0.7,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Chat completion with message history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name (default: llama2)
            temperature: Sampling temperature
            stream: Whether to stream the response
            
        Returns:
            Response dict with 'message' and 'model' keys
        """
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            if stream:
                return {"stream": response.iter_lines(), "model": model}
            else:
                return response.json()
                
        except requests.RequestException as e:
            logger.error(f"Ollama chat failed: {e}")
            raise
    
    def pull_model(self, model: str) -> bool:
        """
        Pull a model from Ollama registry.
        
        Args:
            model: Model name to pull (e.g., 'llama2', 'mistral')
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Pulling model: {model}")
            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": model},
                stream=True,
                timeout=300
            )
            response.raise_for_status()
            
            # Stream pull progress
            for line in response.iter_lines():
                if line:
                    logger.debug(line.decode('utf-8'))
            
            logger.success(f"Model {model} pulled successfully")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to pull model {model}: {e}")
            return False


class LLMProvider:
    """
    Unified LLM provider with automatic fallback.
    
    Attempts to use Ollama for local LLM when available,
    falls back to OpenAI when not.
    """
    
    def __init__(self, config: AASConfig):
        """
        Initialize LLM provider.
        
        Args:
            config: AAS configuration
        """
        self.config = config
        self.ollama = OllamaClient(config)
        self.use_local = self.ollama.is_available()
        
        if self.use_local:
            logger.info("✓ Local LLM (Ollama) available - using local inference")
        else:
            logger.info("Local LLM not available - using OpenAI")
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        prefer_local: bool = True
    ) -> str:
        """
        Generate completion with automatic fallback.
        
        Args:
            prompt: The prompt text
            system: Optional system prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            prefer_local: Try local LLM first if available
            
        Returns:
            Generated text
        """
        if prefer_local and self.use_local:
            try:
                response = self.ollama.generate(
                    prompt=prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return response.get("response", "")
            except Exception as e:
                logger.warning(f"Local LLM failed, falling back to OpenAI: {e}")
        
        # Fallback to OpenAI
        return self._openai_generate(prompt, system, temperature, max_tokens)
    
    def _openai_generate(
        self,
        prompt: str,
        system: Optional[str],
        temperature: float,
        max_tokens: Optional[int]
    ) -> str:
        """Fallback to OpenAI API."""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.config.openai_api_key.get_secret_value())
            
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.config.openai_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI fallback failed: {e}")
            raise
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        prefer_local: bool = True
    ) -> str:
        """
        Chat with message history and automatic fallback.
        
        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            prefer_local: Try local LLM first
            
        Returns:
            Generated response text
        """
        if prefer_local and self.use_local:
            try:
                response = self.ollama.chat(
                    messages=messages,
                    temperature=temperature
                )
                return response.get("message", {}).get("content", "")
            except Exception as e:
                logger.warning(f"Local LLM chat failed, falling back to OpenAI: {e}")
        
        # Fallback to OpenAI
        return self._openai_chat(messages, temperature)
    
    def _openai_chat(self, messages: List[Dict[str, str]], temperature: float) -> str:
        """Fallback to OpenAI chat."""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.config.openai_api_key.get_secret_value())
            
            if self.config.responses_api_enabled:
                # Use new Responses API for chat
                # Convert messages to input format (simplified for now)
                last_user_msg = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
                system_msg = next((m["content"] for m in messages if m["role"] == "system"), "You are a helpful AAS assistant.")
                
                response = client.responses.create(
                    model=self.config.openai_model,
                    instructions=system_msg,
                    input=last_user_msg,
                    temperature=temperature,
                    store=True
                )
                text_outputs = [item.text for item in response.output if hasattr(item, 'text')]
                return "\n".join(text_outputs)
            else:
                response = client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=messages,
                    temperature=temperature
                )
                return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI chat fallback failed: {e}")
            raise
