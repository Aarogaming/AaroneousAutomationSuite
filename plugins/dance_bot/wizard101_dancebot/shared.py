from typing import List


class Globals:
    """For whole program to share a common variable."""
    q_pressed = False
    game_finished = False
    save_settings = False
    resolutions = {
        '800x600': (370, 525, 75, 75),
        '1280x800': (600, 699, 95, 95)
    }
    settings = { key: None for key in ['locations', 'snacks', 'num_games', 'resolution'] }


def separate(string: str, delimiter="=") -> List[str]:
    """Splits the string into 2 parts based on the separater symbol."""
    idx = string.find(delimiter)
    return [
        string[:idx if idx != -1 else len(string)],
        string[idx+1:] if idx != -1 else ""
    ]


def set_save_settings() -> None:
    """Set flag of save_settings in Globals to True."""
    Globals.save_settings = True


def validate_save_settings() -> bool:
    """Return True if and only if settings do not seem like it has been modified externally."""
    import logging
    idx_name_converter = {
        0: 'locations',
        1: 'snacks',
        2: 'num_games',
        3: 'resolution'
    }
    with open('configure.txt', 'r', encoding='utf-8') as fp:
        lines = fp.readlines()
    if len(lines) != 4:
        return False
    for idx, line in enumerate(lines):
        line = line.strip()
        if idx in (0, 1):
            # check locations and snacks
            try:
                line = line.strip(')(').split(', ')
                arr = [int(num) for num in line]
                Globals.settings[idx_name_converter[idx]] = arr[:]
                if any(num not in (0, 1)  for num in arr):
                    return False
            except Exception:
                return False
        elif idx == 2:
            # check number of games
            try:
                Globals.settings[idx_name_converter[idx]] = int(line)
            except Exception:
                return False
        else:
            # check resolution - final check
            try:
                Globals.settings[idx_name_converter[idx]] = line
                return line in Globals.resolutions
            except Exception:
                return False
    # fail safe - shouldn't get here
    message = 'Save settings validation unexpectedly failed.'
    logging.critical(message)
    raise RuntimeError(message)
