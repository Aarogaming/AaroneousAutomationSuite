#!/usr/bin/env python3
"""
Semi-Automated Batch Implementation System
Reads completed batch results and proposes file changes for approval.
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger
import re


DEFAULT_RESULTS_DIR = Path("artifacts/batch/results")


class BatchImplementer:
    """Reads batch results and proposes implementation changes"""

    def __init__(self, results_dir: Optional[Path] = None):
        self.results_dir = results_dir or DEFAULT_RESULTS_DIR
        self.pending_implementations = []

    def load_batch_results(
        self, batch_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Load one or all batch results"""
        if batch_id:
            result_file = self.results_dir / f"{batch_id}_processed.json"
            if not result_file.exists():
                logger.error(f"Batch result not found: {result_file}")
                return []
            with open(result_file, "r", encoding="utf-8") as f:
                return [json.load(f)]
        else:
            # Load all batch results
            results = []
            for result_file in self.results_dir.glob("*_processed.json"):
                with open(result_file, "r", encoding="utf-8") as f:
                    results.append(json.load(f))
            return sorted(results, key=lambda x: x["processed_at"], reverse=True)

    def extract_code_blocks(self, ai_response: str) -> List[Dict[str, str]]:
        """Extract code blocks with file paths from AI response"""
        code_blocks = []

        # Pattern: ```python or ```proto or ``` followed by code
        pattern = r"```(?:python|proto|bash|sh)?\n(.*?)```"
        matches = re.finditer(pattern, ai_response, re.DOTALL)

        for match in matches:
            code = match.group(1).strip()

            # Try to detect file path from context
            # Look for comments like: # In plugin_manager.py or ### file.py
            file_path = None
            lines_before = ai_response[: match.start()].split("\n")[-5:]
            for line in reversed(lines_before):
                # Check for file path indicators
                if "/" in line or "\\" in line or ".py" in line or ".proto" in line:
                    # Extract potential path
                    path_match = re.search(
                        r'[`\'""]?([a-zA-Z_][a-zA-Z0-9_/\\\.]+\.(py|proto|json|md))[`\'"]?',
                        line,
                    )
                    if path_match:
                        file_path = path_match.group(1)
                        break

            code_blocks.append(
                {
                    "file_path": file_path,
                    "code": code,
                    "language": match.group(0).split("\n")[0].replace("```", "").strip()
                    or "python",
                }
            )

        return code_blocks

    def propose_changes(self, task_id: str, ai_response: str) -> List[Dict[str, Any]]:
        """Propose file changes from AI response"""
        proposals = []
        code_blocks = self.extract_code_blocks(ai_response)

        for block in code_blocks:
            if not block["file_path"]:
                # Inferred files need manual path specification
                proposals.append(
                    {
                        "action": "manual_review",
                        "task_id": task_id,
                        "code": block["code"],
                        "reason": "File path could not be determined automatically",
                    }
                )
                continue

            file_path = Path(block["file_path"])

            if file_path.exists():
                # File exists - suggest as update
                proposals.append(
                    {
                        "action": "update",
                        "task_id": task_id,
                        "file_path": str(file_path),
                        "code": block["code"],
                        "language": block["language"],
                    }
                )
            else:
                # New file - suggest creation
                proposals.append(
                    {
                        "action": "create",
                        "task_id": task_id,
                        "file_path": str(file_path),
                        "code": block["code"],
                        "language": block["language"],
                    }
                )

        return proposals

    def analyze_batch_results(
        self, batch_id: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """Analyze batch results and categorize by action type"""
        results = self.load_batch_results(batch_id)

        analysis = {"create": [], "update": [], "manual_review": []}

        for result in results:
            task_ids = result.get("task_ids", [])
            responses = result.get("responses", {})

            for task_id, response in responses.items():
                # Map custom_id back to task ID if needed
                if task_id.startswith("req-"):
                    task_idx = int(task_id.split("-")[1])
                    if task_idx < len(task_ids):
                        task_id = task_ids[task_idx]

                proposals = self.propose_changes(task_id, response)

                for proposal in proposals:
                    action = proposal["action"]
                    analysis[action].append(proposal)

        return analysis

    def generate_implementation_report(self, batch_id: Optional[str] = None) -> str:
        """Generate a human-readable implementation report"""
        analysis = self.analyze_batch_results(batch_id)

        report = ["# Batch Implementation Analysis\n"]

        if batch_id:
            report.append(f"**Batch ID:** {batch_id}\n")
        else:
            report.append("**All Batches**\n")

        report.append("\n## Summary\n")
        report.append(f"- Files to create: {len(analysis['create'])}\n")
        report.append(f"- Files to update: {len(analysis['update'])}\n")
        report.append(f"- Needs manual review: {len(analysis['manual_review'])}\n")

        # Files to create
        if analysis["create"]:
            report.append("\n## 🆕 Files to Create\n")
            for i, item in enumerate(analysis["create"], 1):
                report.append(
                    f"{i}. **{item['file_path']}** (Task: {item['task_id']})\n"
                )
                report.append(f"   - Language: {item['language']}\n")
                report.append(f"   - Lines: {len(item['code'].split(chr(10)))}\n")

        # Files to update
        if analysis["update"]:
            report.append("\n## 🔄 Files to Update\n")
            for i, item in enumerate(analysis["update"], 1):
                report.append(
                    f"{i}. **{item['file_path']}** (Task: {item['task_id']})\n"
                )
                report.append(f"   - Language: {item['language']}\n")
                report.append(
                    f"   - New code lines: {len(item['code'].split(chr(10)))}\n"
                )

        # Manual review needed
        if analysis["manual_review"]:
            report.append("\n## ⚠️ Manual Review Required\n")
            for i, item in enumerate(analysis["manual_review"], 1):
                report.append(f"{i}. **Task {item['task_id']}** - {item['reason']}\n")
                report.append(f"   ```{item.get('language', 'python')}\n")
                report.append(f"   {item['code'][:200]}...\n")
                report.append("   ```\n")

        return "".join(report)


def main():
    """CLI interface for batch implementation"""
    import sys

    implementer = BatchImplementer()

    if len(sys.argv) > 1:
        batch_id = sys.argv[1]
        logger.info(f"Analyzing batch: {batch_id}")
    else:
        batch_id = None
        logger.info("Analyzing all batch results")

    # Generate report
    report = implementer.generate_implementation_report(batch_id)

    # Save report
    report_dir = Path("artifacts/batch/implementation_reports")
    report_dir.mkdir(parents=True, exist_ok=True)

    if batch_id:
        report_file = report_dir / f"{batch_id}_implementation_report.md"
    else:
        report_file = report_dir / "all_batches_implementation_report.md"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)

    logger.success(f"Report saved: {report_file}")
    print(report)


if __name__ == "__main__":
    main()
