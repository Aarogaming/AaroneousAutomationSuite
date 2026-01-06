"""
Quick API connectivity test for OpenAI.
Tests API key validity and basic model access.
"""
import sys
import os
import pytest
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import load_config

def _require_live_api() -> "AASConfig":
    allow = os.getenv("AAS_ALLOW_LIVE_API_TESTS", "").lower() in ("1", "true", "yes")
    if not allow:
        pytest.skip("Live API tests disabled; set AAS_ALLOW_LIVE_API_TESTS=1 to run.")
    try:
        config = load_config()
    except SystemExit:
        pytest.skip("OPENAI_API_KEY missing; skipping live API test.")
    key = config.openai_api_key.get_secret_value()
    if not key or key.strip() == "sk-dummy-key-for-init":
        pytest.skip("OpenAI API key missing or dummy; skipping live API test.")
    return config

def test_api_connection():
    """Test basic OpenAI API connectivity."""
    config = _require_live_api()
    try:
        from openai import OpenAI
        
        logger.info("Loading configuration...")
        logger.info("Initializing OpenAI client...")
        client = OpenAI(api_key=config.openai_api_key.get_secret_value())
        
        logger.info("Testing API connection by listing models...")
        models = client.models.list()
        
        logger.success(f"✓ API connection successful!")
        logger.info(f"  Available models: {models.data[0].id if models.data else 'None'}")
        logger.info(f"  Total models accessible: {len(models.data)}")
        
        # Test a simple completion
        logger.info("Testing simple completion...")
        response = client.chat.completions.create(
            model=config.openai_model,
            messages=[{"role": "user", "content": "Say 'API test successful' if you can read this."}],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        logger.success(f"✓ Completion test successful!")
        logger.info(f"  Model: {config.openai_model}")
        logger.info(f"  Response: {result}")
        
    except ImportError:
        logger.error("✗ OpenAI library not installed. Run: pip install openai")
        raise
    except Exception as e:
        logger.error(f"✗ API test failed: {e}")
        raise

def test_responses_api():
    """Test the new Responses API if enabled."""
    config = _require_live_api()
    try:
        from openai import OpenAI
        
        if not config.responses_api_enabled:
            logger.info("Responses API disabled in config, skipping...")
            return
            
        logger.info("Testing Responses API...")
        client = OpenAI(api_key=config.openai_api_key.get_secret_value())
        
        # Create a stateful response
        response = client.responses.create(
            model=config.openai_model,
            messages=[{"role": "user", "content": "Hello! This is a test."}]
        )
        
        logger.success(f"✓ Responses API test successful!")
        logger.info(f"  Response ID: {response.id}")
        logger.info(f"  Message: {response.output[0].content[0].text if response.output else 'No output'}")
        
    except Exception as e:
        logger.warning(f"⚠ Responses API test failed (may not be available yet): {e}")

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("OpenAI API Connection Test")
    logger.info("=" * 60)
    
    # Test basic connection
    basic_ok = test_api_connection()
    
    if basic_ok:
        # Test Responses API
        test_responses_api()
        
        logger.info("=" * 60)
        logger.success("All tests completed!")
        logger.info("=" * 60)
    else:
        logger.error("Basic API test failed. Check your OPENAI_API_KEY in .env")
        sys.exit(1)
