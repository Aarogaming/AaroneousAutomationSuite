import logging
import random
import time
from typing import List, Tuple

from .shared import Globals

import pyautogui
from .image import *


turn = 0
refresh_rate = 7
moves = []
ARROW_TO_KEY = {
    Arrow.Up: 'up',
    Arrow.Down: 'down',
    Arrow.Left: 'left',
    Arrow.Right: 'right'
}


def load_application(resolution: str) -> None:
    logging.info("Loading application")
    load_textures(resolution)
    generate_subicons()
    remove_duplicate_subicons()
    # This failsafe isn't neccesary as I have built one in already.
    pyautogui.FAILSAFE = False
    logging.info("Finished loading")


def update_search() -> None:
    global moves, turn
    screen = get_screenshot()

    """
    # temporarily removing script functionality
    while len(moves) < turn + 3:
        moves.append(random.choice([arrow for arrow in Arrow]))

    """
    # tries to search using subicons
    for arrow in Arrow:
        for sub_icon in arrow_subicons[arrow.value]:
            # bounds = locate(sub_icon, screen, confidence=0.825)
            bounds = locate(sub_icon, screen, confidence=0.9)

            if bounds is not None:
                moves.append(arrow)
                time.sleep(0.15)  # let time pass for next
    # """

    if len(moves) == turn + 3:
        logging.debug(f"End of round {turn + 1}.")
        time.sleep(0.5)  # give time between finishing and entering keys
        input_moves(moves)
        time.sleep(1.75 + 0.10 * turn)  # wait for game to show next round
        moves = []
        turn += 1

    # there are only five rounds
    if turn == 5:
        time.sleep(1)  # allow time for thread in gui.py read value of turn
        logging.debug("turn now equals 5, triggering the failsafe")
        # pyautogui.moveTo(0, 0)
        turn = 0  # reset turn to zero in-case user wants to play again
        Globals.game_finished = True


def input_moves(input_arrows: List[Arrow]) -> None:
    for arrow in input_arrows:
        pyautogui.press(ARROW_TO_KEY[arrow])
        time.sleep(0.2)


class MouseMover():
    """No need to do error checking since the user will not have access to this class."""

    def __init__(self, locations: List[int], snacks: List[int], resolution: str) -> None:
        self.locations = locations
        self.snacks = snacks
        self.resolution = resolution
        self.mouse_delay = 0.15  # in seconds

    def choose_and_moveto_location(self) -> None:
        available_locations = [
            i for i, location in enumerate(self.locations) if location]
        available_locations = [
            0] if available_locations == [] else available_locations
        location_choice = random.choice(available_locations)
        x, y = MouseMover.get_location_pixels(self.resolution)[location_choice]
        MouseMover.move_and_click(x, y, self.mouse_delay)

    def choose_snack(self) -> int:
        available_snacks = [i for i, snack in enumerate(self.snacks) if snack]
        return random.choice(available_snacks) if available_snacks else -1

    @staticmethod
    def move_and_click(x: int, y: int, mouse_delay: float = 0.15) -> None:
        """Moves mouse to (x, y) in delay seconds and left clicks."""
        pyautogui.moveTo(x, y, mouse_delay)
        pyautogui.click()

    @staticmethod
    def get_location_pixels(resolution: str) -> List[Tuple[int, int]]:
        """These values are hard-coded (x,y)=(0,0)-based coordinates.
        In order, returns the coordinates for Wizard City, Krokotopia, Marleybone, Mooshu, and Dragonspre."""
        x_coords, y = [], 0
        if resolution == '800x600':
            y = 495
            x_coords = [175, 290, 405, 520, 635]
        elif resolution == '1280x800':
            y = 650
            x_coords = [345, 495, 645, 790, 945]
        return [(x, y) for x in x_coords]

    @staticmethod
    def press_right_side_button(resolution: str, mouse_delay: float = 0.15) -> None:
        """Presses PLAY in select level screen,
        NEXT after game finishes,
        and FEED PET in feed screen."""
        x, y = None, None
        if resolution == '800x600':
            x, y = 630, 590
        elif resolution == '1280x800':
            x, y = 940, 770
        MouseMover.move_and_click(x, y, mouse_delay)

    @staticmethod
    def press_left_side_button(resolution: str, mouse_delay: float = 0.15) -> None:
        """Presses CANCEL in select level screen,
        FINISH in both feed screen and post fees screen."""
        x, y = None, None
        if resolution == '800x600':
            x, y = 185, 590
        elif resolution == '1280x800':
            x, y = 355, 770
        MouseMover.move_and_click(x, y, mouse_delay)

    @staticmethod
    def press_snack(snack_index: int, resolution: str, mouse_delay: float = 0.15) -> None:
        """Clicks on the snack given the snack number given (1-5)."""
        x_coords, y = None, None
        if resolution == '800x600':
            pass
        elif resolution == '1280x800':
            y = 540
            x_coords = [350, 495, 655, 790, 940]
        MouseMover.move_and_click(x_coords[snack_index], y, mouse_delay)


class KeyboardPresser():
    """No need to do error checking since the user will not have access to this class."""

    def __init__(self) -> None:
        pass

    def press_key(self, key: str) -> None:
        pyautogui.press(key)
