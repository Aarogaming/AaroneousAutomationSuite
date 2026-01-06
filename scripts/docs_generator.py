"""
Automated Documentation Generator (AAS-223)

Parses docstrings from core managers and generates markdown documentation.
"""

import os
import inspect
import sys
from pathlib import Path
from typing import Dict, List, Any
import re

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

class DocsGenerator:
    """
    Generates documentation for AAS core managers.
    """
    
    def __init__(self, output_dir: str = "docs/api"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.managers_dir = Path("core/managers")
        
    def parse_docstring(self, obj: Any) -> str:
        """Extract and clean docstring from an object."""
        doc = inspect.getdoc(obj)
        return doc if doc else "No documentation provided."

    def generate_manager_docs(self, module_name: str, class_obj: Any):
        """Generate markdown for a specific manager class."""
        name = class_obj.__name__
        doc = self.parse_docstring(class_obj)
        
        md = [
            f"# {name}",
            f"\n{doc}\n",
            "## Methods\n"
        ]
        
        # Get methods
        methods = inspect.getmembers(class_obj, predicate=inspect.isfunction)
        # Also get methods from instances if needed, but usually classes are enough for static analysis
        # For AAS managers, we mostly care about public methods
        
        for m_name, m_func in methods:
            if m_name.startswith('_'):
                continue
                
            m_doc = self.parse_docstring(m_func)
            sig = inspect.signature(m_func)
            
            md.append(f"### `{m_name}{sig}`")
            md.append(f"\n{m_doc}\n")
            
        output_path = self.output_dir / f"{module_name}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
            
        logger.info(f"Generated docs for {name} -> {output_path}")

    def run(self):
        """Run the documentation generation process."""
        logger.info("Starting documentation generation...")
        
        # Import managers dynamically
        import core.task_manager as tasks
        import core.collaboration_manager as collaboration
        import core.knowledge_manager as knowledge
        import core.workspace_manager as workspace
        import core.artifact_manager as artifacts
        import core.batch_manager as batch
        import core.self_healing_manager as self_healing
        import core.protocol_manager as protocol
        
        manager_map = {
            "tasks": (tasks.TaskManager, "TaskManager"),
            "collaboration": (collaboration.AgentCollaborationManager, "AgentCollaborationManager"),
            "knowledge": (knowledge.KnowledgeManager, "KnowledgeManager"),
            "workspace": (workspace.WorkspaceCoordinator, "WorkspaceCoordinator"),
            "artifacts": (artifacts.ArtifactManager, "ArtifactManager"),
            "batch": (batch.BatchManager, "BatchManager"),
            "self_healing": (self_healing.SelfHealingManager, "SelfHealingManager"),
            "protocol": (protocol.AgentHandoffProtocol, "AgentHandoffProtocol")
        }
        
        for mod_name, (cls, _) in manager_map.items():
            try:
                self.generate_manager_docs(mod_name, cls)
            except Exception as e:
                logger.error(f"Failed to generate docs for {mod_name}: {e}")
                
        self.generate_index(manager_map)
        logger.success("Documentation generation complete.")

    def generate_index(self, manager_map: Dict[str, Any]):
        """Generate index.md for the API docs."""
        md = [
            "# AAS API Documentation",
            "\nWelcome to the automated API documentation for Aaroneous Automation Suite core managers.\n",
            "## Core Managers\n"
        ]
        
        for mod_name, (cls, _) in manager_map.items():
            md.append(f"- [{cls.__name__}]({mod_name}.md)")
            
        with open(self.output_dir / "index.md", "w", encoding="utf-8") as f:
            f.write("\n".join(md))
        
        logger.info("Generated API index.")

if __name__ == "__main__":
    generator = DocsGenerator()
    generator.run()
