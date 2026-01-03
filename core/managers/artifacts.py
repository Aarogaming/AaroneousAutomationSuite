"""
Artifact Manager - Shared storage abstraction for multi-client support.

This module provides a unified interface for managing task artifacts,
build outputs, and reports across multiple local clients.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from loguru import logger
from datetime import datetime
from core.managers.protocol import ManagerProtocol


class ArtifactManager(ManagerProtocol):
    """
    Manages the lifecycle and storage of AAS artifacts.
    
    Features:
    - Task-specific artifact directory management
    - Build output organization
    - Report generation and storage
    - Multi-client path resolution
    """
    
    def __init__(self, base_dir: str = "artifacts"):
        self.base_dir = Path(base_dir).resolve()
        self.handoff_dir = self.base_dir / "handoff"
        self.builds_dir = self.base_dir / "builds"
        self.reports_dir = self.handoff_dir / "reports"
        self.ui_audits_dir = self.base_dir / "ui_audits"
        
        self._ensure_dirs()
        logger.info(f"ArtifactManager initialized at {self.base_dir}")

    def _ensure_dirs(self):
        """Ensure core artifact directories exist."""
        for d in [self.handoff_dir, self.builds_dir, self.reports_dir, self.ui_audits_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def get_task_dir(self, task_id: str) -> Path:
        """Get the artifact directory for a specific task."""
        task_dir = self.handoff_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        return task_dir

    def create_task_readme(self, task_id: str, title: str, assignee: str):
        """Initialize a README.md for a new task artifact."""
        task_dir = self.get_task_dir(task_id)
        readme_path = task_dir / "README.md"
        
        if not readme_path.exists():
            content = f"# Task {task_id}: {title}\n\n"
            content += f"**Assignee**: {assignee}\n"
            content += f"**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            content += "## Implementation Summary\n(To be filled by agent)\n\n"
            content += "## Artifacts\n- \n"
            
            with open(readme_path, "w", encoding="utf-8") as f:
                f.write(content)
            logger.debug(f"Created README for task {task_id}")

    def store_report(self, name: str, content: str, sub_dir: str = "reports") -> Path:
        """Store a generated report."""
        target_dir = self.handoff_dir / sub_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = target_dir / name
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logger.info(f"Report stored: {report_path}")
        return report_path

    def get_build_path(self, build_name: str) -> Path:
        """Get path for a build output."""
        return self.builds_dir / build_name

    def cleanup_old_artifacts(self, days: int = 30):
        """Remove artifacts older than specified days (placeholder for future)."""
        logger.info(f"Cleaning up artifacts older than {days} days...")
        # Implementation logic for scanning mtime and unlinking

    # ===== Protocol Implementation =====

    def get_status(self) -> dict:
        """Return ArtifactManager status."""
        return {
            "type": "ArtifactManager",
            "version": "1.0",
            "base_dir": str(self.base_dir),
            "handoff_dir": str(self.handoff_dir)
        }

    def validate(self) -> bool:
        """Validate ArtifactManager state."""
        return self.base_dir.exists()
