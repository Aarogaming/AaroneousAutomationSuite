"""
Test suite for Multi-Modal Research Agent (AAS-108)
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from plugins.ai_assistant.research_agent import MultiModalResearchAgent, ResearchReport
from core.config.manager import load_config


async def test_initialization():
    """Test: Agent initialization"""
    print("TEST: Agent initialization")
    
    try:
        agent = MultiModalResearchAgent()
        assert agent.model == "gpt-4o", "Should use GPT-4o model"
        assert agent.client is not None, "Should have OpenAI client"
        print("[OK] PASS: Agent initialization\n")
        return True
    except Exception as e:
        print(f"[FAIL] Agent initialization: {e}\n")
        return False


async def test_web_search_simulation():
    """Test: Web search (simulated)"""
    print("TEST: Web search simulation")
    
    try:
        agent = MultiModalResearchAgent()
        sources = await agent.web_search("Python async programming", num_results=3)
        
        assert len(sources) == 3, f"Should return 3 sources, got {len(sources)}"
        assert all(hasattr(s, 'url') for s in sources), "All sources should have URLs"
        assert all(hasattr(s, 'title') for s in sources), "All sources should have titles"
        
        print(f"   Found {len(sources)} sources")
        for i, source in enumerate(sources, 1):
            print(f"   {i}. {source.title}")
        
        print("[OK] PASS: Web search simulation\n")
        return True
    except Exception as e:
        print(f"[FAIL] Web search: {e}\n")
        return False


async def test_code_execution_simulation():
    """Test: Code execution (simulated)"""
    print("TEST: Code execution simulation")
    
    try:
        agent = MultiModalResearchAgent()
        result = await agent.execute_code(
            "print('Hello from code interpreter')\nresult = 2 + 2\nprint(f'2 + 2 = {result}')",
            language="python"
        )
        
        assert result['success'] is True, "Code should execute successfully"
        assert 'output' in result, "Should return output"
        print(f"   Output: {result['output'][:100]}...")
        
        print("[OK] PASS: Code execution simulation\n")
        return True
    except Exception as e:
        print(f"[FAIL] Code execution: {e}\n")
        return False


async def test_research_text_only():
    """Test: Text-only research"""
    print("TEST: Text-only research")
    
    try:
        agent = MultiModalResearchAgent()
        report = await agent.research(
            "What are the key features of Pydantic for Python data validation?",
            include_web_search=True,
            include_code_analysis=False
        )
        
        assert isinstance(report, ResearchReport), "Should return ResearchReport"
        assert report.query, "Should have query"
        assert report.summary, "Should have summary"
        assert len(report.sources) > 0, "Should have sources"
        
        print(f"   Query: {report.query}")
        print(f"   Findings: {len(report.findings)}")
        print(f"   Sources: {len(report.sources)}")
        print(f"   Confidence: {report.confidence:.0%}")
        
        print("[OK] PASS: Text-only research\n")
        return True
    except Exception as e:
        print(f"[FAIL] Text-only research: {e}\n")
        return False


async def test_research_with_code():
    """Test: Research with code analysis"""
    print("TEST: Research with code analysis")
    
    try:
        agent = MultiModalResearchAgent()
        report = await agent.research(
            "Analyze Python list comprehension performance",
            include_web_search=False,
            include_code_analysis=True
        )
        
        assert isinstance(report, ResearchReport), "Should return ResearchReport"
        assert len(report.findings) > 0, "Should have findings from code analysis"
        
        print(f"   Findings: {len(report.findings)}")
        print("[OK] PASS: Research with code analysis\n")
        return True
    except Exception as e:
        print(f"[FAIL] Research with code: {e}\n")
        return False


async def test_report_formatting():
    """Test: Report formatting"""
    print("TEST: Report formatting")
    
    try:
        agent = MultiModalResearchAgent()
        report = await agent.research(
            "Test query for formatting",
            include_web_search=True,
            include_code_analysis=False
        )
        
        # Test markdown format
        md = agent.format_report(report, output_format="markdown")
        assert "# Research Report" in md, "Markdown should have header"
        assert "## Summary" in md, "Markdown should have summary section"
        
        # Test JSON format
        import json
        json_str = agent.format_report(report, output_format="json")
        json_data = json.loads(json_str)
        assert "query" in json_data, "JSON should have query field"
        assert "summary" in json_data, "JSON should have summary field"
        
        print("   Markdown format: OK")
        print("   JSON format: OK")
        print("[OK] PASS: Report formatting\n")
        return True
    except Exception as e:
        print(f"[FAIL] Report formatting: {e}\n")
        return False


async def test_image_analysis_mock():
    """Test: Image analysis (mock - skipped if no test image)"""
    print("TEST: Image analysis (mock)")
    
    # Check if test image exists
    test_image = PROJECT_ROOT / "artifacts" / "test_image.png"
    if not test_image.exists():
        print("   [SKIP] No test image found, skipping\n")
        return True
    
    try:
        agent = MultiModalResearchAgent()
        analysis = await agent.analyze_image(
            str(test_image),
            "What is in this image?"
        )
        
        assert isinstance(analysis, str), "Should return string analysis"
        assert len(analysis) > 0, "Analysis should not be empty"
        
        print(f"   Analysis: {analysis[:100]}...")
        print("[OK] PASS: Image analysis\n")
        return True
    except Exception as e:
        print(f"[FAIL] Image analysis: {e}\n")
        return False


async def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("MULTI-MODAL RESEARCH AGENT TEST SUITE (AAS-108)")
    print("=" * 80 + "\n")
    
    tests = [
        test_initialization,
        test_web_search_simulation,
        test_code_execution_simulation,
        test_research_text_only,
        test_research_with_code,
        test_report_formatting,
        test_image_analysis_mock,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"[ERROR] {test.__name__}: {e}\n")
            results.append(False)
    
    passed = sum(results)
    failed = len(results) - passed
    
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 80 + "\n")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
