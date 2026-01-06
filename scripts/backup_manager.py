"""
Backup Manager - AAS System Backup and Restore Utility

This script provides functionality to back up the entire AAS environment,
including configurations, artifacts, and plugins, while respecting
git-friendly file size limits.
"""

import os
import shutil
import zipfile
import tarfile
from pathlib import Path
from datetime import datetime
from loguru import logger

class BackupManager:
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir).resolve()
        self.backup_dir = self.base_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        self.include_dirs = [
            "core/config",
            "artifacts",
            "plugins",
            "handoff",
            "game_manager/maelstrom/ProjectMaelstrom/Resources"
        ]
        
        self.exclude_patterns = [
            "__pycache__",
            ".venv",
            ".git",
            "node_modules",
            "*.pyc",
            "*.tmp",
            "publish",
            "bin",
            "obj"
        ]

    def create_backup(self, label: str = "full") -> Path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"aas_backup_{label}_{timestamp}.zip"
        backup_path = self.backup_dir / backup_name
        
        logger.info(f"Creating backup: {backup_name}...")
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for dir_name in self.include_dirs:
                dir_path = self.base_dir / dir_name
                if not dir_path.exists():
                    logger.warning(f"Directory not found, skipping: {dir_name}")
                    continue
                
                for root, dirs, files in os.walk(dir_path):
                    # Filter excluded directories
                    dirs[:] = [d for d in dirs if not any(p in d for p in self.exclude_patterns)]
                    
                    for file in files:
                        if any(file.endswith(p.replace("*", "")) for p in self.exclude_patterns if "*" in p):
                            continue
                            
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(self.base_dir)
                        
                        # Check size for git-friendliness (warning only for backup)
                        size_mb = file_path.stat().st_size / (1024 * 1024)
                        if size_mb > 50:
                            logger.warning(f"Large file in backup: {arcname} ({size_mb:.2f}MB)")
                            
                        zipf.write(file_path, arcname)
                        
        logger.success(f"Backup created successfully at {backup_path}")
        return backup_path

    def restore_backup(self, backup_path: str):
        path = Path(backup_path)
        if not path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return
            
        logger.info(f"Restoring from {path}...")
        with zipfile.ZipFile(path, 'r') as zipf:
            zipf.extractall(self.base_dir)
        logger.success("Restore complete.")

if __name__ == "__main__":
    manager = BackupManager()
    manager.create_backup()
