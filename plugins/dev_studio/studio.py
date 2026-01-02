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
        Saves results to artifacts/handoff/reports/BUILD_REPORT.md for HealthAggregator.
        """
        try:
            if target == "maelstrom":
                cmd = "dotnet build ../AutoWizard101/ProjectMaelstrom/ProjectMaelstrom.sln"
            else:
                cmd = "pytest"
            
            logger.info(f"DevStudio: Starting build for {target}...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            status = "SUCCESS" if result.returncode == 0 else "FAILED"
            report_content = f"# BUILD REPORT: {target}\nStatus: {status}\n\n## Output\n```\n{result.stdout if result.returncode == 0 else result.stderr}\n```"
            
            report_path = "artifacts/handoff/reports/BUILD_REPORT.md"
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            if result.returncode == 0:
                logger.success(f"DevStudio: Build {target} successful.")
                return result.stdout
            else:
                logger.error(f"DevStudio: Build {target} failed.")
                return result.stderr
        except Exception as e:
            return f"DevStudio Error: {str(e)}"
