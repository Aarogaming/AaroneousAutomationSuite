# Game Automation Plugin Package
# Provides unified interface for Wizard101 automation libraries

from .plugin import GameAutomationPlugin
from .locomotion import LocomotionController
from .wizard_adapter import Wizard101Adapter

__all__ = [
    "GameAutomationPlugin",
    "LocomotionController", 
    "Wizard101Adapter",
]
