"""Public API for Wizard101 DanceBot."""

from typing import Iterable, Sequence


def load(resolution: str = "1280x800") -> int:
    """Validate game window and load properties; returns setup status code."""
    from .main import setup

    return setup(resolution)


def run_games(
    locations: Sequence[int],
    snacks: Sequence[int],
    num_games: int = 1,
    resolution: str = "1280x800",
) -> None:
    """Run games programmatically without showing the GUI."""
    from . import dance_game as DG
    from .main import finish_game, play_game, setup_game
    from .shared import Globals

    DG.load_application(resolution)

    for _ in range(num_games):
        Globals.game_finished = False
        mouse_mover = setup_game(list(locations), list(snacks), resolution)
        play_game()
        finish_game(mouse_mover, resolution)


def run_gui() -> None:
    """Launch the Tk GUI workflow (existing behavior)."""
    from .main import main

    main()


def main() -> None:
    """CLI entry point for `python -m wizard101_dancebot`."""
    run_gui()
