import os
from PIL import Image, ImageChops
from loguru import logger


class VisualAuditBridge:
    """
    Automated GUI Auditing Bridge.
    Performs pixel-diff analysis to detect UI regressions.
    """
    def __init__(self, baseline_dir: str = "ui_baseline",
                 current_dir: str = "ui_current"):
        self.baseline_dir = baseline_dir
        self.current_dir = current_dir

    def compare_snapshots(self, filename: str, threshold: float = 0.5) -> bool:
        """
        Compares a current snapshot against the baseline.
        Returns True if the diff is within the threshold.
        """
        baseline_path = os.path.join(
            self.baseline_dir, filename)
        current_path = os.path.join(
            self.current_dir, filename)

        if not os.path.exists(baseline_path) or not os.path.exists(current_path):
            logger.error(f"VisualAudit: Missing snapshot for {filename}")
            return False

        img1 = Image.open(baseline_path).convert("RGB")
        img2 = Image.open(current_path).convert("RGB")

        diff = ImageChops.difference(img1, img2)
        # Calculate percentage of different pixels
        total_pixels = img1.width * img1.height
        diff_pixels = sum(1 for pixel in diff.getdata() if sum(pixel) > 0)
        diff_percentage = diff_pixels / total_pixels

        if diff_percentage <= threshold:
            logger.success(
                f"VisualAudit: {filename} matches baseline "
                f"(diff: {diff_percentage:.2%}).")
            return True
        else:
            logger.warning(
                f"VisualAudit: Regression detected in {filename} "
                f"(diff: {diff_percentage:.2%}).")
            return False
