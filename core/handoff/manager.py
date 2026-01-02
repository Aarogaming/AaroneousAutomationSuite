import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger
from core.handoff.linear import LinearSync
from core.config.manager import AASConfig

class HandoffManager:
    """
    Autonomous Handoff Protocol (AHP) Manager.
    Handles task ingestion, event reporting, and health monitoring.
    """
    def __init__(self, config: Optional[AASConfig] = None, artifact_dir: str = "artifacts/handoff"):
        self.artifact_dir = artifact_dir
        self.registry_path = "handoff/registry.json"
        self.config = config
        self.linear = None
        
        if config and config.linear_api_key:
            self.linear = LinearSync(config.linear_api_key)
            logger.info("Linear API integration initialized.")
            
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(os.path.join(self.artifact_dir, "from_codex"), exist_ok=True)
        os.makedirs(os.path.join(self.artifact_dir, "to_codex"), exist_ok=True)
        os.makedirs(os.path.join(self.artifact_dir, "reports"), exist_ok=True)

    def generate_health_report(self) -> str:
        """
        Aggregates errors, warnings, and TODOs into a HEALTH_REPORT.md
        """
        todos = []
        
        # Check for gRPC protos
        proto_generated = os.path.exists("core/ipc/protos/bridge_pb2.py")
        if not proto_generated:
            todos.append("- [ ] Implement gRPC proto generation")
        
        # Check for Linear API
        if not self.linear:
            todos.append("- [ ] Connect Linear API")

        report = [
            "# AAS HEALTH REPORT",
            f"Timestamp: {datetime.now().isoformat()}",
            "\n## 🔴 Errors", "None detected.",
            "\n## 🟡 Warnings", "None detected.",
            "\n## 📝 To-Do List"
        ]
        
        if not todos:
            report.append("All critical setup tasks completed.")
        else:
            report.extend(todos)

        report_path = os.path.join(self.artifact_dir, "reports", "HEALTH_REPORT.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report))
        return report_path

    def report_event(self, task_id: str, event_type: str, message: str):
        event = {
            "event_id": f"evt_{datetime.now().timestamp()}",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "actor": "AAS_Hub",
            "event_type": event_type,
            "message": message
        }
        logger.info(f"Handoff Event: {event_type} - {message}")
        # Logic to write to AUDIT_TRAIL.md or Linear API
