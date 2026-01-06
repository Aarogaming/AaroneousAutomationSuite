class MultiModalResearchAgent:
    def __init__(self, *args, **kwargs):
        self.model = "gpt-4o"
        self.client = object()
    async def web_search(self, query, num_results=3):
        class MockSource:
            def __init__(self):
                self.url = "http://example.com"
                self.title = "Mock Title"
        return [MockSource() for _ in range(num_results)]
    async def execute_code(self, code, language="python"):
        return {'success': True, 'output': 'Mock output'}
    async def research(self, query, **kwargs):
        return ResearchReport()
    def format_report(self, report, output_format="markdown"):
        if output_format == "json":
            import json
            return json.dumps({"query": "mock", "summary": "mock"})
        return "# Research Report\n## Summary"
    async def analyze_image(self, path, prompt):
        return "Mock analysis"

class ResearchReport:
    def __init__(self, *args, **kwargs):
        self.query = "Mock query"
        self.summary = "Mock summary"
        self.sources = [object()]
        self.findings = ["Mock finding"]
        self.confidence = 0.9
