"""
Workspace Coordinator - File-system management and cleanup utilities

This module provides:
- Duplicate file detection and removal
- Workspace cleanup and organization
- Runaway bot detection (excessive file creation)
- File pattern analysis and reporting
"""

import os
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict
from loguru import logger


class WorkspaceCoordinator:
    """
    Manages workspace file-system hygiene and organization.
    
    Features:
    - Duplicate file detection (by content hash)
    - Large file identification
    - Temporary file cleanup
    - Runaway bot detection
    - Workspace health reporting
    """
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root).resolve()
        self.ignore_dirs = {
            ".git", ".venv", "__pycache__", "node_modules", 
            ".pytest_cache", ".mypy_cache", "venv", "env",
            "build", "dist", "*.egg-info"
        }
        self.ignore_extensions = {".pyc", ".pyo", ".pyd", ".so", ".dll"}
        self.temp_patterns = ["temp_", "tmp_", ".tmp", "~", ".bak"]
        
        # Runaway bot thresholds
        self.max_files_per_minute = 50
        self.max_duplicates_threshold = 10
        self.max_file_size_mb = 100
        
        logger.info(f"WorkspaceCoordinator initialized for {self.workspace_root}")
    
    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        # Check if any parent directory is in ignore list
        for part in path.parts:
            if part in self.ignore_dirs or part.startswith('.'):
                return True
        
        # Check file extension
        if path.suffix in self.ignore_extensions:
            return True
        
        return False
    
    def _compute_file_hash(self, file_path: Path, chunk_size: int = 8192) -> str:
        """Compute SHA256 hash of file content."""
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash {file_path}: {e}")
            return ""
    
    def find_duplicates(self, scan_dirs: Optional[List[str]] = None) -> Dict[str, List[Path]]:
        """
        Find duplicate files by content hash.
        
        Args:
            scan_dirs: Specific directories to scan, or None for all
            
        Returns:
            Dict mapping hash -> list of file paths with that hash
        """
        logger.info("Scanning for duplicate files...")
        
        if scan_dirs is None:
            scan_paths = [self.workspace_root]
        else:
            scan_paths = [self.workspace_root / d for d in scan_dirs]
        
        hash_map: Dict[str, List[Path]] = defaultdict(list)
        file_count = 0
        
        for scan_path in scan_paths:
            if not scan_path.exists():
                logger.warning(f"Scan path does not exist: {scan_path}")
                continue
            
            for root, dirs, files in os.walk(scan_path):
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
                
                for filename in files:
                    file_path = Path(root) / filename
                    
                    if self._should_ignore(file_path):
                        continue
                    
                    file_hash = self._compute_file_hash(file_path)
                    if file_hash:
                        hash_map[file_hash].append(file_path)
                        file_count += 1
        
        # Filter to only duplicates
        duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
        
        logger.info(f"Scanned {file_count} files, found {len(duplicates)} duplicate sets")
        return duplicates
    
    def find_large_files(self, min_size_mb: float = 10) -> List[Tuple[Path, float]]:
        """
        Find files larger than specified size.
        
        Args:
            min_size_mb: Minimum file size in MB
            
        Returns:
            List of (path, size_mb) tuples
        """
        logger.info(f"Scanning for files larger than {min_size_mb}MB...")
        
        large_files = []
        min_bytes = min_size_mb * 1024 * 1024
        
        for root, dirs, files in os.walk(self.workspace_root):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for filename in files:
                file_path = Path(root) / filename
                
                if self._should_ignore(file_path):
                    continue
                
                try:
                    size = file_path.stat().st_size
                    if size >= min_bytes:
                        size_mb = size / (1024 * 1024)
                        large_files.append((file_path, size_mb))
                except Exception as e:
                    logger.warning(f"Failed to stat {file_path}: {e}")
        
        large_files.sort(key=lambda x: x[1], reverse=True)
        logger.info(f"Found {len(large_files)} large files")
        return large_files
    
    def find_temp_files(self) -> List[Path]:
        """Find temporary files based on naming patterns."""
        logger.info("Scanning for temporary files...")
        
        temp_files = []
        
        for root, dirs, files in os.walk(self.workspace_root):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for filename in files:
                # Check if filename matches temp patterns
                if any(pattern in filename for pattern in self.temp_patterns):
                    file_path = Path(root) / filename
                    if not self._should_ignore(file_path):
                        temp_files.append(file_path)
        
        logger.info(f"Found {len(temp_files)} temporary files")
        return temp_files
    
    def detect_runaway_bot(self, time_window_minutes: int = 5) -> Dict[str, Any]:
        """
        Detect signs of runaway bot activity.
        
        Checks for:
        - Excessive file creation in short time
        - Large number of duplicate files
        - Unusual file patterns
        
        Args:
            time_window_minutes: Time window for recent file check
            
        Returns:
            Dict with detection results and metrics
        """
        logger.info("Checking for runaway bot activity...")
        
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_files = []
        
        for root, dirs, files in os.walk(self.workspace_root):
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for filename in files:
                file_path = Path(root) / filename
                
                if self._should_ignore(file_path):
                    continue
                
                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime >= cutoff_time:
                        recent_files.append((file_path, mtime))
                except Exception:
                    continue
        
        # Check for excessive file creation
        files_per_minute = len(recent_files) / time_window_minutes
        excessive_creation = files_per_minute > self.max_files_per_minute
        
        # Check for duplicate patterns
        if recent_files:
            # Group by directory
            dir_counts = defaultdict(int)
            for file_path, _ in recent_files:
                dir_counts[file_path.parent] += 1
            
            max_files_in_dir = max(dir_counts.values()) if dir_counts else 0
        else:
            max_files_in_dir = 0
        
        # Find duplicate patterns in recent files
        duplicates = self.find_duplicates()
        recent_duplicate_count = 0
        for paths in duplicates.values():
            recent_in_set = sum(1 for p in paths if any(p == rf[0] for rf in recent_files))
            if recent_in_set > 1:
                recent_duplicate_count += recent_in_set
        
        is_runaway = (
            excessive_creation or
            recent_duplicate_count > self.max_duplicates_threshold or
            max_files_in_dir > 100
        )
        
        result = {
            "is_runaway": is_runaway,
            "recent_files_count": len(recent_files),
            "files_per_minute": round(files_per_minute, 2),
            "recent_duplicates": recent_duplicate_count,
            "max_files_in_single_dir": max_files_in_dir,
            "time_window_minutes": time_window_minutes,
            "threshold_exceeded": {
                "excessive_creation": excessive_creation,
                "too_many_duplicates": recent_duplicate_count > self.max_duplicates_threshold,
                "directory_overload": max_files_in_dir > 100
            }
        }
        
        if is_runaway:
            logger.warning(f"Runaway bot detected! Recent files: {len(recent_files)}, "
                         f"Rate: {files_per_minute:.1f}/min")
        else:
            logger.info(f"No runaway activity detected. Recent files: {len(recent_files)}")
        
        return result
    
    def cleanup_duplicates(self, dry_run: bool = True, keep_strategy: str = "newest") -> List[Path]:
        """
        Remove duplicate files, keeping one copy.
        
        Args:
            dry_run: If True, only report what would be deleted
            keep_strategy: "newest", "oldest", or "shortest_path"
            
        Returns:
            List of files that were (or would be) deleted
        """
        duplicates = self.find_duplicates()
        deleted = []
        
        for file_hash, paths in duplicates.items():
            if len(paths) < 2:
                continue
            
            # Determine which file to keep
            if keep_strategy == "newest":
                paths_sorted = sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)
            elif keep_strategy == "oldest":
                paths_sorted = sorted(paths, key=lambda p: p.stat().st_mtime)
            elif keep_strategy == "shortest_path":
                paths_sorted = sorted(paths, key=lambda p: len(str(p)))
            else:
                paths_sorted = list(paths)
            
            keep = paths_sorted[0]
            to_delete = paths_sorted[1:]
            
            logger.info(f"Duplicate set (hash: {file_hash[:8]}...):")
            logger.info(f"  Keeping: {keep}")
            
            for path in to_delete:
                if dry_run:
                    logger.info(f"  Would delete: {path}")
                else:
                    try:
                        path.unlink()
                        logger.success(f"  Deleted: {path}")
                        deleted.append(path)
                    except Exception as e:
                        logger.error(f"  Failed to delete {path}: {e}")
        
        if dry_run:
            logger.info(f"[DRY RUN] Would delete {len(deleted)} duplicate files")
        else:
            logger.success(f"Deleted {len(deleted)} duplicate files")
        
        return deleted
    
    def cleanup_temp_files(self, dry_run: bool = True, age_days: int = 7) -> List[Path]:
        """
        Remove temporary files older than specified age.
        
        Args:
            dry_run: If True, only report what would be deleted
            age_days: Delete files older than this many days
            
        Returns:
            List of files that were (or would be) deleted
        """
        temp_files = self.find_temp_files()
        cutoff_time = datetime.now() - timedelta(days=age_days)
        deleted = []
        
        for file_path in temp_files:
            try:
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff_time:
                    if dry_run:
                        logger.info(f"Would delete temp file: {file_path}")
                    else:
                        file_path.unlink()
                        logger.success(f"Deleted temp file: {file_path}")
                        deleted.append(file_path)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
        
        if dry_run:
            logger.info(f"[DRY RUN] Would delete {len(deleted)} temp files")
        else:
            logger.success(f"Deleted {len(deleted)} temp files")
        
        return deleted

    def defrag_workspace(self, dry_run: bool = True) -> List[str]:
        """
        Ported logic from defrag_workspace.ps1.
        Consolidates build outputs, UI audits, and documentation.
        """
        results = []
        logger.info(f"Starting workspace defragmentation {'(dry run)' if dry_run else ''}...")

        # 1. Consolidate game_manager build outputs
        publish_dir = self.workspace_root / "game_manager/maelstrom/publish"
        if publish_dir.exists():
            target_dir = self.workspace_root / "artifacts/builds/maelstrom_publish"
            if dry_run:
                results.append(f"Would move {publish_dir} to {target_dir}")
            else:
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                shutil.move(str(publish_dir), str(target_dir))
                results.append(f"Moved {publish_dir} to {target_dir}")

        # 2. Consolidate UI audit directories
        ui_dirs = ["game_manager/maelstrom/ui_audit_pack_selfcapture", 
                   "game_manager/maelstrom/ui_baseline", 
                   "game_manager/maelstrom/ui_current"]
        for d in ui_dirs:
            source = self.workspace_root / d
            if source.exists():
                target = self.workspace_root / "artifacts/ui_audits" / source.name
                if dry_run:
                    results.append(f"Would move {source} to {target}")
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    import shutil
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.move(str(source), str(target))
                    results.append(f"Moved {source} to {target}")

        # 3. Consolidate scattered documentation
        doc_source = self.workspace_root / "game_manager/maelstrom"
        if doc_source.exists():
            target_doc_dir = self.workspace_root / "docs/maelstrom"
            doc_files = list(doc_source.glob("*.md"))
            if doc_files:
                if not dry_run:
                    target_doc_dir.mkdir(parents=True, exist_ok=True)
                for doc in doc_files:
                    target = target_doc_dir / doc.name
                    if dry_run:
                        results.append(f"Would copy {doc} to {target}")
                    else:
                        import shutil
                        shutil.copy2(str(doc), str(target))
                        results.append(f"Copied {doc} to {target}")

        return results
    
    def generate_workspace_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive workspace health report.
        
        Returns:
            Dict with workspace metrics and issues
        """
        logger.info("Generating workspace health report...")
        
        # Gather metrics
        duplicates = self.find_duplicates()
        large_files = self.find_large_files(min_size_mb=10)
        temp_files = self.find_temp_files()
        runaway_check = self.detect_runaway_bot()
        
        # Calculate total duplicate waste
        duplicate_waste_mb = 0
        duplicate_file_count = 0
        for paths in duplicates.values():
            if len(paths) > 1:
                size = paths[0].stat().st_size
                duplicate_waste_mb += (size * (len(paths) - 1)) / (1024 * 1024)
                duplicate_file_count += len(paths) - 1
        
        # Calculate temp file waste
        temp_waste_mb = sum(
            f.stat().st_size / (1024 * 1024) 
            for f in temp_files 
            if f.exists()
        )
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "workspace_root": str(self.workspace_root),
            "duplicates": {
                "duplicate_sets": len(duplicates),
                "redundant_files": duplicate_file_count,
                "wasted_space_mb": round(duplicate_waste_mb, 2)
            },
            "large_files": {
                "count": len(large_files),
                "top_10": [
                    {"path": str(p.relative_to(self.workspace_root)), "size_mb": round(s, 2)}
                    for p, s in large_files[:10]
                ]
            },
            "temp_files": {
                "count": len(temp_files),
                "wasted_space_mb": round(temp_waste_mb, 2)
            },
            "runaway_bot_check": runaway_check,
            "health_score": self._calculate_health_score(
                duplicate_waste_mb, temp_waste_mb, runaway_check
            )
        }
        
        return report
    
    def _calculate_health_score(self, duplicate_mb: float, temp_mb: float, 
                                runaway: Dict) -> str:
        """Calculate overall workspace health score."""
        issues = 0
        
        if duplicate_mb > 100:
            issues += 2
        elif duplicate_mb > 50:
            issues += 1
        
        if temp_mb > 50:
            issues += 1
        
        if runaway["is_runaway"]:
            issues += 3
        
        if issues == 0:
            return "Excellent"
        elif issues <= 2:
            return "Good"
        elif issues <= 4:
            return "Fair"
        else:
            return "Needs Attention"
    
    def save_report(self, report: Dict, output_path: str = "artifacts/workspace_health.json"):
        """Save workspace report to file."""
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.success(f"Workspace report saved to {output}")

    # ===== Protocol Implementation =====

    def get_status(self) -> dict:
        """Return WorkspaceCoordinator status."""
        report = self.generate_workspace_report()
        return {
            "type": "WorkspaceCoordinator",
            "version": "1.0",
            "health_score": report["health_score"],
            "root": str(self.workspace_root)
        }

    def validate(self) -> bool:
        """Validate WorkspaceCoordinator state."""
        return self.workspace_root.exists()
