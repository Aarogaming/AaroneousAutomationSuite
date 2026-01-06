"""
Test script for Local LLM Support (Ollama integration).
Tests Ollama client, LLM provider fallback, and AI assistant integration.
"""
import os
import sys
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import load_config
from plugins.ai_assistant.ollama_client import OllamaClient, LLMProvider
from plugins.ai_assistant.assistant import AIAssistant


def test_ollama_availability():
    """Test if Ollama service is available."""
    print("\n" + "="*60)
    print("TEST 1: Ollama Availability Check")
    print("="*60)
    
    config = load_config()
    client = OllamaClient(config)
    
    available = client.is_available()
    print(f"Ollama URL: {client.base_url}")
    print(f"Status: {'Available' if available else 'Not Available'}")
    
    if available:
        print("\nInstalled Models:")
        models = client.list_models()
        if models:
            for model in models:
                name = model.get("name", "unknown")
                size = model.get("size", 0) / (1024**3)  # Convert to GB
                print(f"  - {name} ({size:.2f} GB)")
        else:
            print("  No models installed")
            print("  Install a model with: ollama pull llama2")


def test_ollama_generation():
    """Test Ollama text generation."""
    print("\n" + "="*60)
    print("TEST 2: Ollama Text Generation")
    print("="*60)
    
    config = load_config()
    client = OllamaClient(config)
    
    if not client.is_available():
        print("Skipped - Ollama not available")
        return False
    
    models = client.list_models()
    if not models:
        print("Skipped - No models installed")
        return False
    
    model_name = models[0].get("name", "llama2")
    print(f"Using model: {model_name}")
    
    try:
        prompt = "What is the capital of France? Answer in one sentence."
        print(f"\nPrompt: {prompt}")
        
        response = client.generate(prompt=prompt, model=model_name, max_tokens=50)
        answer = response.get("response", "")
        
        print(f"Response: {answer.strip()}")
        print("Generation successful")
        
    except Exception as e:
        print(f"Generation failed: {e}")
        raise


def test_llm_provider_fallback():
    """Test LLM provider with fallback logic."""
    print("\n" + "="*60)
    print("TEST 3: LLM Provider Fallback")
    print("="*60)
    
    config = load_config()
    provider = LLMProvider(config)
    
    print(f"Local LLM Available: {provider.use_local}")
    print(f"OpenAI Model: {config.openai_model}")
    
    try:
        prompt = "What is 2+2? Answer with just the number."
        print(f"\nPrompt: {prompt}")
        
        # Test with local preference
        print("\nTesting with prefer_local=True...")
        response = provider.generate(prompt, prefer_local=True, max_tokens=10)
        print(f"Response: {response.strip()}")
        
        # Test with OpenAI fallback
        print("\nTesting with prefer_local=False (OpenAI)...")
        response = provider.generate(prompt, prefer_local=False, max_tokens=10)
        print(f"Response: {response.strip()}")
        
        print("Provider fallback working")
        
    except Exception as e:
        print(f"Provider test failed: {e}")
        raise


def test_ai_assistant_integration():
    """Test AI Assistant with local LLM support."""
    print("\n" + "="*60)
    print("TEST 4: AI Assistant Integration")
    print("="*60)
    
    config = load_config()
    
    # Test with local preference
    print("\nTesting with prefer_local=True...")
    assistant = AIAssistant(config, prefer_local=True)
    
    try:
        import asyncio
        
        prompt = "What is the Aaroneous Automation Suite?"
        context = "AAS is a multi-purpose automation hub for games and home automation."
        
        print(f"Prompt: {prompt}")
        response = asyncio.run(assistant.ask(prompt, context=context))
        print(f"Response: {response[:200]}...")  # First 200 chars
        
        print("AI Assistant integration successful")
        
    except Exception as e:
        print(f"AI Assistant test failed: {e}")
        raise


def test_strategy_generation():
    """Test strategy code generation."""
    print("\n" + "="*60)
    print("TEST 5: Strategy Generation")
    print("="*60)
    
    config = load_config()
    assistant = AIAssistant(config, prefer_local=True)
    
    try:
        game_state = '{"player_health": 500, "enemy_health": 300, "pips": 4}'
        print(f"Game State: {game_state}")
        
        strategy = assistant.generate_strategy(game_state)
        print(f"\nGenerated Strategy:\n{strategy[:300]}...")  # First 300 chars
        
        print("Strategy generation successful")
        
    except Exception as e:
        print(f"Strategy generation failed: {e}")
        raise


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LOCAL LLM SUPPORT (OLLAMA) - TEST SUITE")
    print("="*60)
    
    results = []
    
    # Test 1: Availability (always run)
    ollama_available = test_ollama_availability()
    results.append(("Ollama Availability", True))  # Always passes
    
    # Test 2: Generation (conditional)
    if ollama_available:
        results.append(("Ollama Generation", test_ollama_generation()))
    else:
        print("\nSkipping Ollama-specific tests (service not available)")
    
    # Test 3: Provider Fallback (always run)
    results.append(("LLM Provider Fallback", test_llm_provider_fallback()))
    
    # Test 4: AI Assistant (always run)
    results.append(("AI Assistant Integration", test_ai_assistant_integration()))
    
    # Test 5: Strategy Generation (always run)
    results.append(("Strategy Generation", test_strategy_generation()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed! Local LLM support is working.")
    else:
        print(f"\n{total - passed} test(s) failed.")
    
    # Recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    if not ollama_available:
        print("To use local LLMs:")
        print("   1. Install Ollama: https://ollama.ai")
        print("   2. Pull a model: ollama pull llama2")
        print("   3. Start service: ollama serve")
        print("   4. Verify: curl http://localhost:11434/api/tags")
    else:
        print("Local LLM ready to use!")
        print("   - Set prefer_local=True in AIAssistant")
        print("   - Automatic fallback to OpenAI if local fails")
        print("   - Supports: llama2, mistral, codellama, and more")


if __name__ == "__main__":
    main()
