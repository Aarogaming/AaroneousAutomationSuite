"""
Git Size Checker - AAS Utility

Uses WorkspaceCoordinator to verify that all files in the repository
respect the 50MB git-friendly size limit.
"""

import sys
from pathlib import Path
from core.managers.workspace import WorkspaceCoordinator
from loguru import logger

def main():
    coordinator = WorkspaceCoordinator(workspace_root=".")
    report = coordinator.check_git_compatibility()
    
    print(f"\n--- Git Compatibility Report (Limit: {report['limit_mb']}MB) ---")
    if report["is_compatible"]:
        logger.success("All files are git-repo size-friendly!")
        sys.exit(0)
    else:
        logger.warning(f"Found {len(report['issues'])} size issues:")
        for issue in report["issues"]:
            print(f"  • {issue['path']}: {issue['size_mb']}MB")
            print(f"    Recommendation: {issue['recommendation']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
