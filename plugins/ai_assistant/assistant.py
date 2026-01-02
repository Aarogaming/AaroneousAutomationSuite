import openai
from pydantic import SecretStr
from loguru import logger
from typing import Optional, Any
from core.config.manager import AASConfig
from plugins.ai_assistant.ollama_client import LLMProvider


class AIAssistant:
    """
    Onboard AI Assistant with local LLM support.
    Provides context-aware help and strategy generation.
    Supports both OpenAI and local Ollama models with automatic fallback.
    """
    def __init__(self, config: AASConfig, prefer_local: bool = True):
        """
        Initialize AI Assistant.
        
        Args:
            config: AAS configuration
            prefer_local: Prefer local LLM when available
        """
        self.config = config
        self.prefer_local = prefer_local
        self.llm_provider = LLMProvider(config)
        self.model = config.openai_model
        
        # Legacy OpenAI client for direct access when needed
        self.client = openai.OpenAI(api_key=config.openai_api_key.get_secret_value())

    async def ask(self, prompt: str, context: str = "", use_local: Optional[bool] = None) -> str:
        """
        Ask the AI assistant a question.
        
        Args:
            prompt: User question
            context: Additional context to provide
            use_local: Override prefer_local setting
            
        Returns:
            AI response
        """
        try:
            prefer_local = use_local if use_local is not None else self.prefer_local
            
            system_prompt = f"You are the AAS Onboard Assistant. Context: {context}"
            
            logger.info(f"Querying AI assistant (local={prefer_local})...")
            
            response = self.llm_provider.generate(
                prompt=prompt,
                system=system_prompt,
                temperature=0.7,
                prefer_local=prefer_local
            )
            
            return response
            
        except Exception as e:
            logger.error(f"AI Assistant query failed: {e}")
            return "I'm sorry, I encountered an error while processing your request."

    def generate_strategy(self, game_state_json: str, use_local: Optional[bool] = None) -> str:
        """
        Generates DeimosLang code based on game state.
        
        Args:
            game_state_json: JSON representation of game state
            use_local: Override prefer_local setting
            
        Returns:
            Generated strategy code
        """
        try:
            prefer_local = use_local if use_local is not None else self.prefer_local
            
            system_prompt = "You are an expert at generating DeimosLang automation code for Wizard101."
            prompt = f"Generate DeimosLang strategy code for this game state:\n{game_state_json}"
            
            response = self.llm_provider.generate(
                prompt=prompt,
                system=system_prompt,
                temperature=0.5,  # Lower temperature for code generation
                prefer_local=prefer_local
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Strategy generation failed: {e}")
            return "// Strategy generation failed - check logs for details."
    
    def chat(self, messages: list[dict[str, str]], use_local: Optional[bool] = None) -> str:
        """
        Multi-turn conversation with message history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            use_local: Override prefer_local setting
            
        Returns:
            AI response
        """
        try:
            prefer_local = use_local if use_local is not None else self.prefer_local
            
            response = self.llm_provider.chat(
                messages=messages,
                temperature=0.7,
                prefer_local=prefer_local
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return "I'm sorry, I encountered an error during our conversation."
