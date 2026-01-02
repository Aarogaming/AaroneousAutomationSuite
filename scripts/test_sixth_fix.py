"""
Test script to verify Sixth AI assistant fix.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config.manager import load_config
from plugins.ai_assistant.ollama_client import LLMProvider
from loguru import logger

def test_chat():
    """Test basic chat functionality."""
    config = load_config()
    provider = LLMProvider(config)
    
    print("\n" + "="*60)
    print("Testing Sixth AI Assistant Chat")
    print("="*60 + "\n")
    
    # Test with Responses API disabled
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'Hello, I am working!' in one sentence."}
    ]
    
    logger.info(f"Responses API Enabled: {config.responses_api_enabled}")
    logger.info("Sending test message...")
    
    try:
        response = provider.chat(
            messages=messages,
            prefer_local=False  # Force OpenAI
        )
        
        print(f"\n✅ SUCCESS!")
        print(f"Response: {response['content']}")
        print(f"Model: {response['model']}")
        print(f"Response ID: {response.get('response_id', 'N/A')}")
        
        if not response['content'].strip():
            print("\n⚠️ WARNING: Empty response content!")
            return False
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        logger.exception("Test failed")
        return False

if __name__ == "__main__":
    success = test_chat()
    sys.exit(0 if success else 1)
