import subprocess
import os
from typing import Optional, List
from loguru import logger

class GitKrakenCLI:
    """
    Wrapper for GitKraken CLI (gk.exe).
    Enables Git workflow automation and workspace management.
    """
    def __init__(self, executable_path: str = "c:/Users/aarog/Downloads/gk_3.1.48_windows_amd64/gk.exe"):
        self.gk = executable_path
        if not os.path.exists(self.gk):
            logger.warning(f"GitKraken CLI not found at {self.gk}. Some features will be disabled.")

    def _run(self, args: List[str]) -> Optional[str]:
        """Runs a gk command and returns the output."""
        if not os.path.exists(self.gk):
            return None
            
        try:
            result = subprocess.run([self.gk] + args, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"GitKraken CLI error: {e.stderr}")
            return None

    def get_version(self) -> Optional[str]:
        """Returns the gk version."""
        return self._run(["--version"])

    def create_branch(self, branch_name: str) -> bool:
        """Creates a new branch via gk."""
        logger.info(f"GitKraken: Creating branch {branch_name}")
        result = self._run(["branch", "create", branch_name])
        return result is not None

    def create_pr(self, title: str, body: str) -> bool:
        """Creates a pull request via gk."""
        logger.info(f"GitKraken: Creating PR '{title}'")
        result = self._run(["pr", "create", "--title", title, "--description", body])
        return result is not None

    def list_issues(self) -> Optional[str]:
        """Lists issues from connected providers (Linear/GitHub)."""
        return self._run(["issue", "list"])
