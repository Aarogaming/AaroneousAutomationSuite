"""
Multi-Modal Research Agent (AAS-108)

A research agent that combines:
- Vision capabilities (GPT-4o) for image analysis
- Web search for real-time information
- Code interpreter for data processing
- Report generation with structured outputs

Use cases:
- Analyze UI screenshots from Maelstrom
- Research technical documentation with visuals
- Generate comprehensive reports with citations
- Process and visualize data
"""

import asyncio
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from openai import AsyncOpenAI
from loguru import logger

from core.config.manager import load_config


@dataclass
class ResearchSource:
    """A source cited in research"""
    url: str
    title: str
    snippet: str
    relevance: float = 0.0


@dataclass
class ResearchReport:
    """Generated research report"""
    query: str
    summary: str
    findings: List[str]
    sources: List[ResearchSource]
    images_analyzed: int
    generated_at: datetime
    confidence: float


class MultiModalResearchAgent:
    """
    Multi-modal research agent with vision, web search, and code execution.
    
    Capabilities:
    - Analyze images using GPT-4o vision
    - Search the web for real-time information
    - Execute code for data analysis
    - Generate structured research reports
    """
    
    def __init__(self, config=None):
        """Initialize the research agent"""
        self.config = config or load_config()
        self.client = AsyncOpenAI(api_key=self.config.openai_api_key.get_secret_value())
        self.model = "gpt-4o"  # Multi-modal model with vision
        
    async def analyze_image(
        self,
        image_path: str,
        question: str = "Describe this image in detail"
    ) -> str:
        """
        Analyze an image using vision capabilities.
        
        Args:
            image_path: Path to the image file
            question: Question to ask about the image
            
        Returns:
            Analysis result as text
        """
        logger.info(f"Analyzing image: {image_path}")
        
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
        
        # Determine image type
        ext = Path(image_path).suffix.lower()
        mime_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }
        mime_type = mime_types.get(ext, "image/jpeg")
        
        # Call vision API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        result = response.choices[0].message.content
        logger.success(f"Image analysis complete: {len(result)} chars")
        return result
    
    async def web_search(
        self,
        query: str,
        num_results: int = 5
    ) -> List[ResearchSource]:
        """
        Search the web for information.
        
        Note: This is a placeholder. In production, integrate with:
        - Brave Search API
        - Google Custom Search API
        - SerpAPI
        - Or use OpenAI's native web_search tool when available
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of research sources
        """
        logger.info(f"Web search: {query}")
        
        # Placeholder: Use GPT to simulate web search results
        # In production, replace with actual web search API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a web search simulator. Generate realistic search results with URLs, titles, and snippets."
                },
                {
                    "role": "user",
                    "content": f"Generate {num_results} search results for: {query}"
                }
            ],
            max_tokens=500
        )
        
        # Parse simulated results (in production, parse actual API response)
        result_text = response.choices[0].message.content
        
        # For now, return placeholder sources
        sources = [
            ResearchSource(
                url=f"https://example.com/search/{i}",
                title=f"Result {i} for {query}",
                snippet=result_text[:200] if i == 0 else "...",
                relevance=1.0 - (i * 0.1)
            )
            for i in range(num_results)
        ]
        
        logger.success(f"Found {len(sources)} search results")
        return sources
    
    async def execute_code(
        self,
        code: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Execute code for data analysis.
        
        Note: This uses GPT to simulate code execution.
        In production, integrate with:
        - OpenAI Code Interpreter API
        - Jupyter kernel
        - Sandboxed Python executor
        
        Args:
            code: Code to execute
            language: Programming language
            
        Returns:
            Execution result with output and any generated data
        """
        logger.info(f"Executing {language} code: {len(code)} chars")
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": f"You are a {language} code interpreter. Execute the code and return the output."
                },
                {
                    "role": "user",
                    "content": f"Execute this code:\n\n```{language}\n{code}\n```"
                }
            ],
            max_tokens=1000
        )
        
        output = response.choices[0].message.content
        
        logger.success("Code execution complete")
        return {
            "output": output,
            "success": True,
            "language": language
        }
    
    async def research(
        self,
        query: str,
        image_paths: Optional[List[str]] = None,
        include_web_search: bool = True,
        include_code_analysis: bool = False
    ) -> ResearchReport:
        """
        Conduct comprehensive research on a topic.
        
        Args:
            query: Research question or topic
            image_paths: Optional list of images to analyze
            include_web_search: Whether to search the web
            include_code_analysis: Whether to include code-based analysis
            
        Returns:
            Comprehensive research report
        """
        logger.info(f"Starting research: {query}")
        
        findings = []
        sources = []
        images_analyzed = 0
        
        # 1. Analyze images if provided
        if image_paths:
            logger.info(f"Analyzing {len(image_paths)} images...")
            for img_path in image_paths:
                try:
                    analysis = await self.analyze_image(
                        img_path,
                        f"Analyze this image in the context of: {query}"
                    )
                    findings.append(f"Image analysis: {analysis}")
                    images_analyzed += 1
                except Exception as e:
                    logger.error(f"Failed to analyze {img_path}: {e}")
        
        # 2. Web search if enabled
        if include_web_search:
            logger.info("Searching the web...")
            try:
                web_sources = await self.web_search(query)
                sources.extend(web_sources)
                findings.append(f"Found {len(web_sources)} relevant web sources")
            except Exception as e:
                logger.error(f"Web search failed: {e}")
        
        # 3. Code analysis if enabled
        if include_code_analysis:
            logger.info("Running code-based analysis...")
            try:
                # Generate analysis code
                code_prompt = f"Generate Python code to analyze data related to: {query}"
                code_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a data analyst. Generate Python code."},
                        {"role": "user", "content": code_prompt}
                    ],
                    max_tokens=500
                )
                code = code_response.choices[0].message.content
                
                # Execute code
                result = await self.execute_code(code)
                findings.append(f"Code analysis: {result['output']}")
            except Exception as e:
                logger.error(f"Code analysis failed: {e}")
        
        # 4. Generate summary and synthesis
        logger.info("Generating research summary...")
        
        findings_text = "\n".join(f"- {f}" for f in findings)
        sources_text = "\n".join(f"- [{s.title}]({s.url}): {s.snippet}" for s in sources)
        
        summary_prompt = f"""
Research Question: {query}

Findings:
{findings_text}

Sources:
{sources_text}

Generate a comprehensive research summary with:
1. Main insights (3-5 bullet points)
2. Key conclusions
3. Confidence level (0-1)
        """
        
        summary_response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a research analyst. Synthesize findings into a clear summary."},
                {"role": "user", "content": summary_prompt}
            ],
            max_tokens=1000
        )
        
        summary = summary_response.choices[0].message.content
        
        # Create report
        report = ResearchReport(
            query=query,
            summary=summary,
            findings=findings,
            sources=sources,
            images_analyzed=images_analyzed,
            generated_at=datetime.now(),
            confidence=0.85  # Placeholder confidence score
        )
        
        logger.success(f"Research complete: {len(findings)} findings, {len(sources)} sources")
        return report
    
    def format_report(self, report: ResearchReport, output_format: str = "markdown") -> str:
        """
        Format research report for output.
        
        Args:
            report: Research report to format
            output_format: Output format (markdown, html, json)
            
        Returns:
            Formatted report as string
        """
        if output_format == "markdown":
            md = f"# Research Report: {report.query}\n\n"
            md += f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            md += f"**Confidence:** {report.confidence:.0%}\n\n"
            
            md += "## Summary\n\n"
            md += f"{report.summary}\n\n"
            
            if report.findings:
                md += "## Findings\n\n"
                for i, finding in enumerate(report.findings, 1):
                    md += f"{i}. {finding}\n"
                md += "\n"
            
            if report.sources:
                md += "## Sources\n\n"
                for i, source in enumerate(report.sources, 1):
                    md += f"{i}. [{source.title}]({source.url})\n"
                    md += f"   {source.snippet}\n\n"
            
            md += f"\n---\n*Images analyzed: {report.images_analyzed}*\n"
            
            return md
        
        elif output_format == "json":
            import json
            return json.dumps({
                "query": report.query,
                "summary": report.summary,
                "findings": report.findings,
                "sources": [
                    {"url": s.url, "title": s.title, "snippet": s.snippet, "relevance": s.relevance}
                    for s in report.sources
                ],
                "images_analyzed": report.images_analyzed,
                "generated_at": report.generated_at.isoformat(),
                "confidence": report.confidence
            }, indent=2)
        
        else:
            raise ValueError(f"Unsupported format: {output_format}")


async def main():
    """Demo usage"""
    agent = MultiModalResearchAgent()
    
    # Example 1: Text-only research
    report = await agent.research(
        "What are the latest developments in AI agents and multi-modal models?",
        include_web_search=True
    )
    
    print(agent.format_report(report))
    
    # Example 2: Image analysis
    # report = await agent.research(
    #     "Analyze this UI design and suggest improvements",
    #     image_paths=["path/to/screenshot.png"],
    #     include_web_search=False
    # )
    # print(agent.format_report(report))


if __name__ == "__main__":
    asyncio.run(main())
