"""
Benchmark script for testing local AI model performance.

This script evaluates various local models (Ollama, LocalAI) across different
hardware configurations to help users choose the right model for their setup.
"""

import asyncio
import time
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import httpx
from loguru import logger
from tabulate import tabulate

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import load_config


class ModelBenchmark:
    """Benchmark local AI models for performance and quality."""
    
    def __init__(self, endpoint: str = "http://localhost:11434"):
        """
        Initialize benchmark tool.
        
        Args:
            endpoint: Ollama or LocalAI endpoint URL
        """
        self.endpoint = endpoint
        self.results: List[Dict] = []
    
    async def benchmark_model(
        self,
        model: str,
        test_prompts: List[str],
        num_runs: int = 3
    ) -> Dict:
        """
        Benchmark a specific model.
        
        Args:
            model: Model name (e.g., "mistral", "codellama")
            test_prompts: List of test prompts
            num_runs: Number of runs per prompt for averaging
        
        Returns:
            Dictionary with benchmark results
        """
        logger.info(f"Benchmarking model: {model}")
        
        results = {
            "model": model,
            "avg_tokens_per_sec": 0.0,
            "avg_latency_ms": 0.0,
            "max_memory_mb": 0.0,
            "success_rate": 0.0,
            "test_results": []
        }
        
        total_tokens_per_sec = 0.0
        total_latency = 0.0
        successful_runs = 0
        
        for prompt in test_prompts:
            for run in range(num_runs):
                try:
                    # Run inference
                    start_time = time.time()
                    
                    async with httpx.AsyncClient(timeout=120.0) as client:
                        response = await client.post(
                            f"{self.endpoint}/api/generate",
                            json={
                                "model": model,
                                "prompt": prompt,
                                "stream": False
                            }
                        )
                        response.raise_for_status()
                        data = response.json()
                    
                    elapsed = time.time() - start_time
                    
                    # Calculate metrics
                    response_text = data.get("response", "")
                    tokens = len(response_text.split())  # Approximate
                    tokens_per_sec = tokens / elapsed if elapsed > 0 else 0
                    
                    total_tokens_per_sec += tokens_per_sec
                    total_latency += elapsed * 1000  # Convert to ms
                    successful_runs += 1
                    
                    results["test_results"].append({
                        "prompt": prompt[:50] + "...",
                        "tokens": tokens,
                        "tokens_per_sec": tokens_per_sec,
                        "latency_ms": elapsed * 1000,
                        "success": True
                    })
                    
                    logger.debug(f"Run {run+1}/{num_runs}: {tokens_per_sec:.1f} tokens/sec")
                    
                except Exception as e:
                    logger.error(f"Failed run {run+1}/{num_runs}: {e}")
                    results["test_results"].append({
                        "prompt": prompt[:50] + "...",
                        "tokens": 0,
                        "tokens_per_sec": 0,
                        "latency_ms": 0,
                        "success": False,
                        "error": str(e)
                    })
        
        # Calculate averages
        total_runs = len(test_prompts) * num_runs
        if successful_runs > 0:
            results["avg_tokens_per_sec"] = total_tokens_per_sec / successful_runs
            results["avg_latency_ms"] = total_latency / successful_runs
            results["success_rate"] = (successful_runs / total_runs) * 100
        
        logger.info(f"Model '{model}': {results['avg_tokens_per_sec']:.1f} tokens/sec, "
                   f"{results['success_rate']:.0f}% success rate")
        
        return results
    
    async def run_benchmarks(
        self,
        models: List[str],
        test_type: str = "code"
    ) -> None:
        """
        Run benchmarks on multiple models.
        
        Args:
            models: List of model names to test
            test_type: "code", "chat", or "reasoning"
        """
        logger.info(f"Starting benchmarks for {len(models)} models")
        logger.info(f"Test type: {test_type}")
        
        # Select test prompts based on type
        test_prompts = self._get_test_prompts(test_type)
        
        # Benchmark each model
        for model in models:
            try:
                result = await self.benchmark_model(model, test_prompts)
                self.results.append(result)
            except Exception as e:
                logger.error(f"Failed to benchmark {model}: {e}")
        
        # Display results
        self._display_results()
    
    def _get_test_prompts(self, test_type: str) -> List[str]:
        """Get test prompts based on test type."""
        prompts = {
            "code": [
                "Write a Python function to calculate Fibonacci numbers",
                "Explain the difference between async and sync functions in Python",
                "Refactor this code for better performance: def slow_func(): return [i*2 for i in range(1000000)]"
            ],
            "chat": [
                "What is the capital of France?",
                "Explain quantum computing in simple terms",
                "Write a short story about a robot learning to paint"
            ],
            "reasoning": [
                "If I have 5 apples and give away 2, then buy 3 more, how many do I have?",
                "What is the pattern: 2, 4, 8, 16, ?",
                "Solve this riddle: I speak without a mouth and hear without ears. I have no body, but I come alive with wind. What am I?"
            ]
        }
        return prompts.get(test_type, prompts["code"])
    
    def _display_results(self) -> None:
        """Display benchmark results in a table."""
        if not self.results:
            logger.warning("No results to display")
            return
        
        logger.info("\n" + "="*80)
        logger.info("BENCHMARK RESULTS")
        logger.info("="*80)
        
        # Summary table
        summary_data = []
        for result in self.results:
            summary_data.append([
                result["model"],
                f"{result['avg_tokens_per_sec']:.1f}",
                f"{result['avg_latency_ms']:.0f}",
                f"{result['success_rate']:.0f}%"
            ])
        
        headers = ["Model", "Tokens/sec", "Latency (ms)", "Success Rate"]
        print("\n" + tabulate(summary_data, headers=headers, tablefmt="grid"))
        
        # Hardware tier recommendation
        print("\n" + "="*80)
        print("HARDWARE TIER RECOMMENDATIONS")
        print("="*80)
        
        for result in self.results:
            tokens_per_sec = result["avg_tokens_per_sec"]
            tier = self._recommend_tier(tokens_per_sec)
            print(f"\n{result['model']}: {tier}")
    
    def _recommend_tier(self, tokens_per_sec: float) -> str:
        """Recommend hardware tier based on performance."""
        if tokens_per_sec < 10:
            return "⚠️  Tier 1 (Entry) - Performance may be slow for complex tasks"
        elif tokens_per_sec < 20:
            return "✓  Tier 1 (Entry) - Suitable for basic development"
        elif tokens_per_sec < 30:
            return "✓  Tier 2 (Enthusiast) - Good for full development workflow"
        else:
            return "✓✓ Tier 3 (Professional) - Excellent for multi-agent orchestration"


async def main():
    """Main benchmark execution."""
    logger.info("Local AI Model Benchmark Tool")
    logger.info("="*80)
    
    # Load config
    try:
        config = load_config()
        endpoint = config.ollama_url or "http://localhost:11434"
    except Exception as e:
        logger.warning(f"Could not load config: {e}. Using default endpoint.")
        endpoint = "http://localhost:11434"
    
    logger.info(f"Endpoint: {endpoint}")
    
    # Check if Ollama is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.get(f"{endpoint}/api/tags")
        logger.info("✓ Ollama is running")
    except Exception:
        logger.error("✗ Ollama is not running. Please start Ollama first.")
        logger.info("  Run: ollama serve")
        return
    
    # Get available models
    logger.info("\nFetching available models...")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{endpoint}/api/tags")
            response.raise_for_status()
            data = response.json()
            available_models = [model["name"] for model in data.get("models", [])]
        
        if not available_models:
            logger.warning("No models found. Please pull models first.")
            logger.info("  Example: ollama pull mistral")
            return
        
        logger.info(f"Found {len(available_models)} models:")
        for model in available_models:
            logger.info(f"  - {model}")
    
    except Exception as e:
        logger.error(f"Failed to fetch models: {e}")
        return
    
    # Select models to benchmark
    print("\n" + "="*80)
    print("Select models to benchmark (comma-separated numbers, or 'all'):")
    for i, model in enumerate(available_models, 1):
        print(f"  {i}. {model}")
    
    selection = input("\nSelection: ").strip().lower()
    
    if selection == "all":
        models_to_test = available_models
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(",")]
            models_to_test = [available_models[i] for i in indices]
        except (ValueError, IndexError):
            logger.error("Invalid selection")
            return
    
    # Select test type
    print("\n" + "="*80)
    print("Select test type:")
    print("  1. Code generation")
    print("  2. Chat/conversation")
    print("  3. Reasoning")
    
    test_type_input = input("\nSelection (1-3): ").strip()
    test_type_map = {"1": "code", "2": "chat", "3": "reasoning"}
    test_type = test_type_map.get(test_type_input, "code")
    
    # Run benchmarks
    benchmark = ModelBenchmark(endpoint=endpoint)
    await benchmark.run_benchmarks(models_to_test, test_type=test_type)
    
    logger.info("\n✓ Benchmarking complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nBenchmark cancelled by user")
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
