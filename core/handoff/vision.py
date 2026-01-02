import base64
import os
from typing import Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from loguru import logger
from core.config.manager import AASConfig

class VisionClient:
    """
    Multi-Modal Vision Client for AAS.
    Enables the suite to "see" and describe game screenshots or UI elements.
    """
    def __init__(self, config: AASConfig):
        self.config = config
        self.llm = ChatOpenAI(
            model="gpt-4o", # Using gpt-4o for high-performance vision
            api_key=config.openai_api_key.get_secret_value(),
            max_tokens=500
        )

    def _encode_image(self, image_path: str) -> str:
        """Encodes an image to base64."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    async def describe_screenshot(self, image_path: str, prompt: Optional[str] = None) -> str:
        """
        Sends a screenshot to the vision model and returns a description.
        """
        if not os.path.exists(image_path):
            logger.error(f"Vision: Image not found at {image_path}")
            return "Error: Image not found."

        logger.info(f"Vision: Analyzing screenshot {image_path}...")
        
        base64_image = self._encode_image(image_path)
        
        default_prompt = "Describe this game screenshot in detail. Focus on UI elements, player health/mana, and the current environment."
        final_prompt = prompt or default_prompt

        message = HumanMessage(
            content=[
                {"type": "text", "text": final_prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ]
        )

        try:
            response = await self.llm.ainvoke([message])
            return str(response.content)
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}")
            return f"Error: {e}"

    async def detect_ui_elements(self, image_path: str) -> Dict[str, Any]:
        """
        Specific prompt to extract UI state as structured-like text.
        """
        prompt = """
        Analyze this Wizard101 screenshot and extract the following information in a structured format:
        - Player Health (Current/Max)
        - Player Mana (Current/Max)
        - Active Quest Name
        - Current Location
        - Visible NPCs or Enemies
        """
        description = await self.describe_screenshot(image_path, prompt)
        # In a future iteration, we would use structured output (JSON) here.
        return {"raw_description": description}
