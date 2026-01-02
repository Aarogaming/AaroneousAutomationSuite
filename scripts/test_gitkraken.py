import os
import sys
from loguru import logger

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.handoff.gitkraken import GitKrakenCLI

def main():
    """
    Test script for GitKraken CLI integration.
    """
    logger.info("Testing GitKraken CLI Integration...")
    
    gk = GitKrakenCLI()
    version = gk.get_version()
    
    if version:
        logger.success(f"GitKraken CLI detected: {version}")
        # Test issue listing (requires auth, might fail but verifies wrapper)
        logger.info("Attempting to list issues...")
        issues = gk.list_issues()
        if issues:
            logger.info(f"Issues found:\n{issues}")
        else:
            logger.warning("No issues found or auth required.")
            
        logger.success("GitKraken integration test completed.")
    else:
        logger.error("GitKraken CLI not functional. Check path in core/handoff/gitkraken.py")

if __name__ == "__main__":
    main()
