import os
import re
from loguru import logger

class HealthAggregator:
    """
    Scans the codebase for TODOs, FIXMEs, and HACKs.
    Aggregates them into the HEALTH_REPORT.md.
    """
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.patterns = {
            "TODO": re.compile(r"TODO[:\s]+(.*)", re.IGNORECASE),
            "FIXME": re.compile(r"FIXME[:\s]+(.*)", re.IGNORECASE),
            "HACK": re.compile(r"HACK[:\s]+(.*)", re.IGNORECASE)
        }

    def scan(self) -> dict:
        results = {"TODO": [], "FIXME": [], "HACK": []}
        for root, _, files in os.walk(self.root_dir):
            if any(x in root for x in [".git", "__pycache__", "venv", "bin", "obj"]):
                continue
            
            for file in files:
                if not file.endswith((".py", ".cs", ".proto", ".md")):
                    continue
                
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        for i, line in enumerate(f, 1):
                            for key, pattern in self.patterns.items():
                                match = pattern.search(line)
                                if match:
                                    results[key].append(f"{file}:{i} - {match.group(1).strip()}")
                except Exception as e:
                    logger.warning(f"HealthAggregator: Could not read {path}: {e}")
        
        return results
