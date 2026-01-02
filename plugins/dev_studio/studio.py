import os
import subprocess
from loguru import logger

class DevStudio:
    """
    AAS Dev Studio (Compact Sixth).
    Provides internal code editing and terminal hooks for self-building.
    """
    def __init__(self, project_root: str = "."):
        self.project_root = project_root

    def run_build(self, target: str = "maelstrom") -> str:
        """
        Executes a build command from within AAS.
        """
        try:
            if target == "maelstrom":
                cmd = "dotnet build ../AutoWizard101/ProjectMaelstrom/ProjectMaelstrom.sln"
            else:
                cmd = "pytest"
            
            logger.info(f"DevStudio: Starting build for {target}...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.success(f"DevStudio: Build {target} successful.")
                return result.stdout
            else:
                logger.error(f"DevStudio: Build {target} failed.")
                return result.stderr
        except Exception as e:
            return f"DevStudio Error: {str(e)}"

    def save_file(self, relative_path: str, content: str):
        """
        Internal editor save hook.
        """
        full_path = os.path.join(self.project_root, relative_path)
        with open(full_path, "w") as f:
            f.write(content)
        logger.info(f"DevStudio: Saved {relative_path}")
