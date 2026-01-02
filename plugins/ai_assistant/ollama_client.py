"""
Ollama Local LLM Client for AAS.

Provides a unified interface for interacting with locally-hosted LLMs via Ollama.
Supports fallback to OpenAI when local models are unavailable.
Migrated to OpenAI Responses API for better performance and agentic capabilities.
"""
import requests
from typing import Optional, Dict, Any, List, Union
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
        prefer_local: bool = True,
        previous_response_id: Optional[str] = None,
        tools: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Chat with message history and automatic fallback.
        
        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            prefer_local: Try local LLM first
            previous_response_id: ID of previous response for stateful chat
            tools: List of tools for the model to use
            
        Returns:
            Dict containing 'content', 'response_id', and 'model'
        """
        if prefer_local and self.use_local:
            try:
                response = self.ollama.chat(
                    messages=messages,
                    temperature=temperature
                )
                return {
                    "content": response.get("message", {}).get("content", ""),
                    "response_id": None,
                    "model": response.get("model", "local")
                }
            except Exception as e:
                logger.warning(f"Local LLM chat failed, falling back to OpenAI: {e}")
        
        # Fallback to OpenAI
        return self._openai_chat(
            messages=messages, 
            temperature=temperature,
            previous_response_id=previous_response_id,
            tools=tools
        )

    def _openai_chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float,
        previous_response_id: Optional[str] = None,
        tools: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """Fallback to OpenAI chat using either Responses API or Chat Completions."""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.config.openai_api_key.get_secret_value())
            
            if self.config.responses_api_enabled:
                # Use new Responses API for stateful, tool-enabled chat
                # Convert messages to input items
                input_items: List[Any] = []
                for msg in messages:
                    if msg["role"] == "user":
                        input_items.append({
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": msg["content"]}]
                        })
                
                # Extract system instructions
                instructions = next((m["content"] for m in messages if m["role"] == "system"), "You are a helpful AAS assistant.")
                
                # Configure native tools
                native_tools: List[Any] = []
                if self.config.enable_web_search:
                    native_tools.append({"type": "web_search"})
                # File search requires vector_store_ids which we don't have yet
                # if self.config.enable_file_search:
                #     native_tools.append({"type": "file_search"})
                # Code interpreter seems to require 'container' parameter in some environments
                # if self.config.enable_code_interpreter:
                #     native_tools.append({"type": "code_interpreter"})
                
                # Combine with custom tools if provided
                all_tools = native_tools + (tools or [])
                
                response = client.responses.create(
                    model=self.config.openai_model,
                    instructions=instructions,
                    input=input_items,
                    tools=all_tools if all_tools else None, # type: ignore
                    temperature=temperature,
                    previous_response_id=previous_response_id,
                    store=True  # Enable stateful context
                )
                
                # Extract text content and response ID
                text_content = ""
                tool_calls_info = []
                
                for item in response.output:
                    if hasattr(item, 'type'):
                        if item.type == "message":
                            # In Responses API, message items have a content list
                            if hasattr(item, 'content'):
                                for part in item.content: # type: ignore
                                    if hasattr(part, 'type'):
                                        if part.type == "output_text" and hasattr(part, 'text'):
                                            text_content += part.text # type: ignore
                                        elif part.type == "text" and hasattr(part, 'text'):
                                            text_content += part.text # type: ignore
                        elif item.type.endswith("_call"):
                            # Handle tool calls (web_search_call, function_call, etc.)
                            tool_calls_info.append(item.type)
                            logger.debug(f"Tool call: {item.type}")
                
                if tool_calls_info:
                    logger.info(f"✓ Responses API executed tools: {', '.join(tool_calls_info)}")
                
                return {
                    "content": text_content,
                    "response_id": response.id,
                    "model": response.model,
                    "tool_calls": tool_calls_info
                }
            else:
                # Legacy Chat Completions API
                response = client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=messages, # type: ignore
                    temperature=temperature,
                    tools=tools if tools else None # type: ignore
                )
                return {
                    "content": response.choices[0].message.content or "",
                    "response_id": None,
                    "model": response.model,
                    "tool_calls": []
                }
            
        except Exception as e:
            logger.error(f"OpenAI chat fallback failed: {e}")
            raise
