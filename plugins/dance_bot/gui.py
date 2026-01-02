from dataclasses import astuple, dataclass, field
from functools import wraps
import inspect
import logging
from logging import config
import sys
import threading
from typing import Any, Callable, List

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import font, messagebox

import dance_game as DG
import shared
from shared import Globals


def self_destruct(func: Callable) -> Callable:
    """Delay root.destroy() until after the message box is shown."""
    @wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        result = func(self, *args, **kwargs)
        if hasattr(self, 'destruct') and inspect.ismethod(self.destruct):
            self.destruct()
        return result
    return wrapper


class MessageBox():
    """Shows message box without the root window."""

    def __init__(self, title: str, message: str) -> None:
        self.title = title
        self.message = message

        self.root = tk.Tk()
        self.root.overrideredirect(1)
        self.root.withdraw()

    def destruct(self) -> None:
        self.root.destroy()

    @self_destruct
    def show_error(self) -> None:
        logging.error(self.title, stacklevel=4)
        messagebox.showerror(title=self.title, message=self.message)

    @self_destruct
    def show_warning(self) -> None:
        logging.warning(self.title, stacklevel=4)
        messagebox.showwarning(title=self.tilte, message=self.message)

    @self_destruct
    def show_info(self) -> None:
        logging.info(self.title, stacklevel=4)
        messagebox.showinfo(title=self.title, message=self.message)


def create_frame(master: tk.Frame, **kwargs) -> tk.Frame:
    return tk.Frame(master, bg=kwargs.get('bg', '#f0f0f0'), relief='raised')


class EntryWithPlaceholder(tk.Entry):
    def __init__(self, master: tk.Frame = None, placeholder: str = 'PLACEHOLDER', color: str = 'grey', text=None) -> None:
        super().__init__(master)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']
        self['justify'] = 'left'

        self.bind("<FocusIn>", self.focus_in)
        self.bind("<FocusOut>", self.focus_out)

        # not a placeholder, use text value if specified
        if text is not None:
            self.insert(tk.END, text)
        else:
            self.put_placeholder()

    def put_placeholder(self) -> None:
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def focus_in(self, *args) -> None:
        if self['fg'] == self.placeholder_color:
            self.delete('0', 'end')
            self['fg'] = self.default_fg_color

    def focus_out(self, *args) -> None:
        if not self.get():
            self.put_placeholder()


@dataclass
class ConfigureSettings:
    locations: List[int] = field(default_factory=list)
    snacks: List[int] = field(default_factory=list)
    num_games: int = 1
    resolution: str = ''

    def __iter__(self):
        """Returns the data as a tuple."""
        return iter(astuple(self))


class Configure(tk.Tk):
    configure_settings: ConfigureSettings = None

    def __init__(self) -> None:
        super().__init__()
        self.title("W101 Pet Dance")
        self.geometry("268x248")
        # open window in center of screen
        self.eval('tk::PlaceWindow . center')
        self.resizable(False, False)
        self.columnconfigure(0, weight=1)  # column weight 100%
        self.rowconfigure(0, weight=5)
        self.rowconfigure(1, weight=2)  # change weight to 4
        self.rowconfigure(2, weight=1)
        self.protocol("WM_DELETE_WINDOW", lambda: sys.exit(0))
        self.fg_color = '#171c21'
        self.bg_color = '#ececec'

        # adding frames to window
        frame_top = create_frame(self)
        frame_middle = create_frame(self)
        frame_bottom = create_frame(self)
        frame_topleft = create_frame(frame_top)
        frame_topright = create_frame(frame_top)
        frame_middleleft = create_frame(frame_middle)
        frame_middleright = create_frame(frame_middle)
        frame_bottomleft = create_frame(frame_bottom)
        frame_bottomright = create_frame(frame_bottom)

        # placing in grid
        frame_top.columnconfigure(0, weight=1)
        frame_top.columnconfigure(1, weight=1)
        frame_top.rowconfigure(0, weight=1)
        frame_top.grid(row=0, column=0, sticky='nesw')
        frame_topleft.grid(row=0, column=0, sticky='nesw')
        frame_topright.grid(row=0, column=1, sticky='nesw')

        frame_middle.columnconfigure(0, weight=1)
        frame_middle.columnconfigure(1, weight=1)
        frame_middle.rowconfigure(0, weight=1)
        frame_middle.grid(row=1, column=0, sticky='nesw')
        frame_middleleft.grid(row=0, column=0, sticky='nesw')
        frame_middleright.grid(row=0, column=1, sticky='nesw')

        frame_bottom.columnconfigure(0, weight=1)
        frame_bottom.columnconfigure(1, weight=1)
        frame_bottom.rowconfigure(0, weight=1)
        frame_bottom.grid(row=2, column=0, sticky='nesw')
        frame_bottomleft.grid(row=0, column=0, sticky='nesw')
        frame_bottomright.grid(row=0, column=1, sticky='nesw')

        # validate configure file before consider using it
        self.valid_settings = shared.validate_save_settings()

        # add location check boxes
        self.frame_locations(frame_topleft)

        # add snack check boxes
        self.frame_snacks(frame_topright)

        # add "configurations"
        self.configure_games(frame_middleleft)
        self.configure_resolutions(frame_middleright)

        tk.Button(frame_bottomleft, text='Save', command=shared.set_save_settings, relief='solid',
                  fg=self.fg_color, highlightbackground='#e1e1e1').pack(expand=True, fill='both', padx=10, pady=10)
        tk.Button(frame_bottomright, text='Start', command=self.start, relief='solid',
                  fg=self.fg_color, highlightbackground='#e1e1e1').pack(expand=True, fill='both', padx=10, pady=10)
        logging.info("Finished configuration")

    def frame_locations(self, frame: tk.Frame) -> None:
        logging.debug("Configuring locations")
        self.location_boxes = []
        tk.Label(frame, text='Locations to Farm', fg=self.fg_color, bg=self.bg_color,
                 font=font.Font(size=9, underline=True)).pack(padx=10, pady=(10, 0), anchor='w')
        cities = ['Wizard City', 'Krokotopia', 'Marleybone', 'Mooshu', 'Dragonspyre']

        # three way nested ternary -> L = a if A else (b if B else c)
        location_values = Globals.settings['locations'] if self.valid_settings else \
            Configure.configure_settings.locations if Configure.configure_settings is not None else [None] * len(cities)
        locations = zip(cities, location_values)

        # use default settings or previously entered settings or previously saved settings
        for idx, (city, location_checked) in enumerate(locations):
            self.location_boxes.append(tk.IntVar(value=location_checked))
            self.create_checkbox(frame, anchor='w', text=city, var=self.location_boxes[idx])

    def frame_snacks(self, frame: tk.Frame) -> None:
        logging.debug("Configuring snacks")
        self.snack_boxes = []
        tk.Label(frame, text='Pet Snacks to Feed', fg=self.fg_color, bg=self.bg_color,
                 font=font.Font(size=9, underline=True)).pack(padx=10, pady=(10, 0), anchor='e')
        snacks_names = [f'Snack {i}' for i in range(1, 6)]

        # three way nested ternary
        snack_values = Globals.settings['snacks'] if self.valid_settings else \
            Configure.configure_settings.snacks if Configure.configure_settings is not None else [None] * len(snacks_names)
        snacks = zip(snacks_names, snack_values)

        # use default settings or previously entered settings or previously saved settings
        for idx, (snack, snack_checked) in enumerate(snacks):
            self.snack_boxes.append(tk.IntVar(value=snack_checked))
            self.create_checkbox(frame, anchor='center', text=snack, var=self.snack_boxes[idx])

    def configure_games(self, frame: tk.Frame) -> None:
        logging.debug("Configuring number of games")
        tk.Label(frame, text='Amount of Games', fg=self.fg_color, bg=self.bg_color,
                 font=font.Font(size=9, underline=True)).pack(padx=10, pady=0, anchor='w')

        # three way nested ternary
        num_games_text = Globals.settings['num_games'] if self.valid_settings else \
            (None if Configure.configure_settings is None or Configure.configure.settings.num_games == 1 else \
            Configure.configure.num_games)

        # use default settings or previously entered settings or previously saved settings
        self.games = EntryWithPlaceholder(frame, placeholder="1", text=num_games_text)
        self.games.pack(padx=12, pady=0, anchor='w')

    def configure_resolutions(self, frame: tk.Frame) -> None:
        logging.debug("Configuring resolution")
        available_resolutions = [*Globals.resolutions.keys()]
        tk.Label(frame, text='Resolution', fg=self.fg_color, bg=self.bg_color,
                 font=font.Font(size=9, underline=True)).pack(padx=10, pady=0, anchor='w')
        self.resolutions = ttk.Combobox(frame, value=available_resolutions, width=16, state='readonly',
                                        foreground=self.fg_color, background=self.bg_color)
        self.resolutions.pack(padx=(12, 18))

        # three way nested ternary
        # use default settings or previously entered settings or previously saved settings
        self.resolutions.current(available_resolutions.index(Globals.settings['resolution'] if self.valid_settings else \
            (Configure.configure_settings.resolution if Configure.configure_settings is not None else available_resolutions[0])))

    def create_checkbox(self, master: tk.Frame, *, anchor: str, text: str, var: tk.IntVar) -> None:
        tk.Checkbutton(master, text=text, variable=var, pady=0,
                       fg=self.fg_color, bg=self.bg_color).pack(padx=10, anchor=anchor)

    def start(self) -> None:
        # get selections on location
        locations = tuple(var.get() for var in self.location_boxes)

        # get selections on snack
        snacks = tuple(var.get() for var in self.snack_boxes)

        # get number of games
        num_games = None
        games = self.games.get()
        if games == '':
            num_games = 1
        else:
            try:
                num_games = max(1, int(games))
            except ValueError:
                num_games = 1

        # get resolution
        resolution = self.resolutions.get()
        Configure.configure_settings = ConfigureSettings(
            locations=locations, snacks=snacks, num_games=num_games, resolution=resolution)

        try:
            self.destroy()
        except Exception:
            pass


class Playing(tk.Tk):
    def __init__(self, resolution: str, num_games: int, current_game: int) -> None:
        width, height = shared.separate(resolution, delimiter='x')
        super().__init__()
        self.title('W101 Pet Dance')
        self.geometry(f"300x130+{width}+{int(height) // 10 * 7}")
        self.resizable(False, False)
        self.columnconfigure(0, weight=1)
        for i in range(3):
            self.rowconfigure(i, weight=1)
        self.bind('q', lambda key: self.stop())
        self.protocol("WM_DELETE_WINDOW", lambda: self.stop())

        # adding frames to window
        frame_top = create_frame(self)
        frame_middle = create_frame(self)
        frame_bottom = create_frame(self)

        # placing in grid
        frame_top.grid(row=0, column=0, sticky='nesw')
        frame_middle.grid(row=1, column=0, sticky='nesw')
        frame_bottom.rowconfigure(0, weight=1)
        frame_bottom.columnconfigure(0, weight=1)
        frame_bottom.columnconfigure(1, weight=1)
        frame_bottom.grid(row=2, column=0, sticky='nesw')

        padx = 16
        self.progress_bar = ttk.Progressbar(
            frame_middle, orient='horizontal', mode='determinate', length=300-2*padx)
        self.progress_bar.grid(columnspan=3, padx=padx, pady=0)

        self.label = ttk.Label(frame_top, text=self.update_progress_label(),
                               font=font.Font(size=12, weight='bold'))
        self.label.grid(columnspan=3, padx=padx, pady=(10, 0))

        # for bottom frame
        games_progress = ttk.Label(
            frame_bottom, text=f"Game {current_game + 1} of {num_games}", font=font.Font(size=11, weight='bold'))
        games_progress.grid(row=0, column=0, padx=padx, pady=(0, 10), sticky='w')

        caption = ttk.Label(frame_bottom, text="(press 'q' to quit)")
        caption.grid(row=0, column=1, padx=padx, pady=(0, 10), sticky='w')

        # for self.interval_update()
        self.prev = 0
        self.finished = False

    def update_progress_label(self) -> str:
        return f"Current Progress: {self.progress_bar['value']}%"

    def progress(self) -> None:
        if self.progress_bar['value'] < 100:
            self.progress_bar['value'] += 20
            self.label['text'] = self.update_progress_label()
        if self.progress_bar['value'] == 100:
            self.finished = True

    def stop(self) -> None:
        try:
            # since self.progress() might call self.stop() before self.check_progress_thread() does
            # thus we would be attempting to update a label that is already destroyed
            self.label['text'] = self.update_progress_label()
            logging.info("Destroying Playing() widget")
            self.destroy()
        except Exception as exception:
            logging.error(repr(exception))

    def start_progress_thread(self, thread: threading.Thread) -> None:
        self.after(1000, lambda: self.check_progress_thread(thread))

    def check_progress_thread(self, thread: threading.Thread) -> None:
        if thread.is_alive() and not Globals.q_pressed:
            self.interval_update()
            self.after(200, lambda: self.check_progress_thread(thread))
        else:
            logging.debug('thread is dead - progress bar stopped (thread)')
            self.stop()

    def interval_update(self) -> None:
        if DG.turn <= 5:
            if DG.turn != self.prev:
                # new round
                self.progress()
                self.prev += 1
