import atexit
import inspect
import logging
import os
import sys
import time
import threading
from typing import List

import pyautogui
import pygetwindow as pgw
from pynput import keyboard

from . import logger  # noqa: F401 - configure logging on import
from . import dance_game as DG
from .shared import Globals
from .gui import MessageBox
from .properties import separate


def setup_game(locations: List[int], snacks: List[int], resolution: str) -> DG.MouseMover:
    MM = DG.MouseMover(locations, snacks, resolution)
    KP = DG.KeyboardPresser()

    # press 'X' to play
    KP.press_key('x')

    # choose location from user input
    MM.choose_and_moveto_location()

    # press play
    MM.press_right_side_button(resolution)

    # wait for page turn animation
    time.sleep(1.6)
    return MM


def finish_game(MM: DG.MouseMover, resolution: str) -> None:
    # stats improvement screen, just click next
    MM.press_right_side_button(resolution)
    snack_index = MM.choose_snack()

    # either feed snack, or finish
    if snack_index == -1:
        MM.press_left_side_button(resolution)
    else:
        MM.press_snack(snack_index, resolution)
        MM.press_right_side_button(resolution)


def play_game() -> None:
    application_closed = False
    while not application_closed and not Globals.game_finished:
        DG.update_search()

        # Amount of time in seconds required for each frame.
        frame_duration = 1.0 / DG.refresh_rate
        time.sleep(frame_duration)

        # Emergency exit the program when the mouse is in the top left corner
        mousex, mousey = pyautogui.position()
        application_closed = mousex + mousey == 0


def setup(resolution: str) -> int:
    """Return value meanings:
    0 - successful return
    1 - error, resolution do not match
    2 - error already thrown (could not find Wizard101 client)
    These will be the only return values from this function.
    """
    # assuming the user only has one instance of title wizard101 running
    EPSILON = 15  # tolerance
    offsetX, offsetY = 10, 30
    DG.properties.load_file(resolution=resolution)

    try:
        possible_windows = pgw.getWindowsWithTitle('Wizard101')
        for window in possible_windows:
            if window.title == 'Wizard101':
                w101_window = window
                break
        else:
            raise IndexError("Wizard101 Graphical Client not found.")

        sizeX, sizeY = w101_window.size
        width, height = sizeX - offsetX, sizeY - offsetY
        actual_width, actual_height = separate(resolution, delimiter='x')

        if abs(int(actual_width) - width) >= EPSILON:
            return 1
        if abs(int(actual_height) - height) >= EPSILON:
            return 1

        w101_window.activate()
        w101_window.moveTo(0, 0)
    except IndexError:
        MessageBox(title='Game Not Found',
                   message='Could not find Wizard101 client running on your computer.').show_error()
        return 2

    return 0


def main() -> None:
    from .gui import Configure, Playing
    # listen for keyboard inputs
    threading.Thread(target=key_listener, daemon=True).start()

    while True:
        config = Configure()
        config.mainloop()
        locations, snacks, num_games, resolution = Configure.configure_settings

        # overwrite file if user chooses to save current settings
        if Globals.save_settings:
            Globals.save_settings = False
            with open('configure.txt', 'w', encoding='utf-8') as fp:
                fp.writelines([f'{str(setting)}\n' for setting in Configure.configure_settings])
            logging.info("Finished saving settings to configure.txt")

        if not any(locations):
            MessageBox(title='Invalid Selection',
                       message='Select at least one area to play').show_info()
            continue
        return_value = setup(resolution)

        # save configuration settings to reuse after the script has finished playing
        if return_value in [1, 2]:
            if return_value == 1:
                MessageBox(title='Invalid Resolution',
                           message='Game resolution and selected resolution do not match up.').show_error()
            continue
        try:
            DG.load_application(resolution)
        except Exception as exception:
            logging.error(repr(exception))
            MessageBox(title='Application Load Fail',
                       message='Failed to load application, now closing.').show_error()
            return

        logging.debug(f"{num_games = }")
        for game_index in range(0, num_games):
            logging.debug(f"Playing Game {game_index + 1} of {num_games}")
            Globals.game_finished = False
            MM = setup_game(locations, snacks, resolution)

            logging.info('running Playing() in main')
            play = Playing(resolution, num_games, game_index)

            progress_thread = threading.Thread(target=play_game, daemon=False)
            progress_thread.start()
            play.after(100, lambda: play.start_progress_thread(progress_thread))

            play.mainloop()
            progress_thread.join()  # wait for thread to finish before continuing
            logging.debug(
                f'{progress_thread.is_alive() = }\t{play.finished = }')
            logging.info('finishing Playing().mainloop()')

            # execute feed snack only if user did not early stop
            if play.finished:
                logging.info('play was finished, running post game movement')
                finish_game(MM, resolution)
                time.sleep(2)  # give time for animation
            else:
                logging.critical("Uncaught break - play.finished returned False.")
                break


def on_press(key: any) -> None:
    logging.trace('Key %s pressed' % key, stacklevel=3)
    try:
        if key.char == 'q':
            Globals.q_pressed = True
            logging.debug("Quitting application because q key pressed")
            os._exit(1)
    except AttributeError:
        pass


def key_listener() -> None:
    logging.debug("Started keyboard listener")
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


def check_running_instance() -> None:
    """Raise error if instance is already running."""
    app_title = "W101 Pet Dance"
    if not pgw.getWindowsWithTitle(app_title):
        return
    MessageBox(title='Duplicate application',
               message='A dance bot instance is already running on your computer').show_error()
    raise RuntimeError("An instance is already running.")


if __name__ == "__main__":
    try:
        check_running_instance()
        main()
    except Exception as exception:
        logging.critical(repr(exception))
