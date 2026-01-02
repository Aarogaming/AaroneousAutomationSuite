import openai
from pydantic import SecretStr
from loguru import logger

class AIAssistant:
    """
    Onboard AI Assistant using GPT-5.2 Pro.
    Provides context-aware help and strategy generation.
    """
    def __init__(self, api_key: SecretStr, model: str = "gpt-5.2-pro"):
        self.client = openai.OpenAI(api_key=api_key.get_secret_value())
        self.model = model

    async def ask(self, prompt: str, context: str = "") -> str:
        try:
            logger.info(f"Querying {self.model} for user assistance...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are the AAS Onboard Assistant. Context: {context}"},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI Assistant query failed: {e}")
            return "I'm sorry, I encountered an error while processing your request."

    def generate_strategy(self, game_state_json: str) -> str:
        """
        Generates DeimosLang code based on game state.
        """
        # Logic to prompt GPT-5.2 for DeimosLang output
        return "// Strategy generation logic pending implementation."
