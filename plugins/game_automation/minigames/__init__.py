# Minigames Library
# Game-specific trainers and automation presets for Wizard101

from .base import MinigameTrainer, MinigameConfig
from .dance_game import DanceGameTrainer
from .fishing import FishingTrainer
from .gardening import GardeningTrainer

__all__ = [
    "MinigameTrainer",
    "MinigameConfig",
    "DanceGameTrainer",
    "FishingTrainer",
    "GardeningTrainer",
    "TRAINERS",
    "get_trainer",
]

# Registry of available minigame trainers
TRAINERS = {
    "dance": DanceGameTrainer,
    "pet_dance": DanceGameTrainer,  # alias
    "fishing": FishingTrainer,
    "gardening": GardeningTrainer,
}


def get_trainer(name: str) -> type:
    """Get a trainer class by name."""
    trainer = TRAINERS.get(name.lower())
    if not trainer:
        available = ", ".join(TRAINERS.keys())
        raise ValueError(f"Unknown trainer '{name}'. Available: {available}")
    return trainer
