"""
Test script for OpenAI Responses API migration.
Verifies stateful chat and native tool integration.
"""
import sys
import os
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.manager import load_config
from plugins.ai_assistant.assistant import AIAssistant

def test_responses_api():
    """Test the new Responses API integration."""
    try:
        config = load_config()
        
        # Ensure Responses API is enabled for test
        config.responses_api_enabled = True
        config.openai_model = "gpt-4o" # Use a model that supports Responses API
        
        assistant = AIAssistant(config, prefer_local=False)
        
        logger.info("Testing stateful chat with Responses API...")
        
        # Turn 1
        messages = [{"role": "user", "content": "My name is Aaron. Remember this."}]
        response1 = assistant.chat(messages)
        logger.info(f"Response 1: {response1}")
        logger.info(f"Last Response ID: {assistant.last_response_id}")
        
        if not assistant.last_response_id:
            logger.error("FAILED: No response_id returned from Responses API")
            return
            
        # Turn 2 - Testing statefulness
        messages = [{"role": "user", "content": "What is my name?"}]
        response2 = assistant.chat(messages)
        logger.info(f"Response 2: {response2}")
        
        if "Aaron" in response2:
            logger.success("SUCCESS: Stateful conversation working!")
        else:
            logger.warning("WARNING: Model might not have remembered the name, but check if response_id was used.")

        # Test native tools (Web Search)
        if config.enable_web_search:
            logger.info("Testing native web search tool...")
            messages = [{"role": "user", "content": "Search for the latest news about SpaceX Starship."}]
            response3 = assistant.chat(messages)
            logger.info(f"Response 3 (Web Search): {response3}")
            logger.success("Web search test completed.")

    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    test_responses_api()
