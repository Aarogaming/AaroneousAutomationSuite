import argparse
import logging
import sys


# Configure logging and arg parsing
LOGGER = logging.getLogger(__name__)
parser = argparse.ArgumentParser(
    prog="Wizard101 Dance Bot",
    description="Auto pet dancer",
)
parser.add_argument('-d', '--dev-mode', action='store_true',
                    help='Enable dev mode (logs to stdout)')
args = parser.parse_args()


def addLoggingLevel(levelName: str, levelNum: int, methodName: str = None) -> None:
    """
    Taken from: https://stackoverflow.com/a/35804945/17918212

    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG + 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    15

    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
        raise AttributeError(
            '{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
        raise AttributeError(
            '{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError(
            '{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        # stacklevel=2 skips an additional stack frame so that the function name is not this one.
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)


# adding a level above debug but below info
addLoggingLevel(levelName="TRACE", levelNum=5)


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    blue = "\x1b[34m"
    magenta = "\x1b[35m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    FORMATS = {
        level: "%(asctime)s %(levelname_brackets)-10s %(stack_format)s %(message)s"
        for level in [logging.TRACE, logging.DEBUG, logging.INFO,
                      logging.WARNING, logging.ERROR, logging.CRITICAL]
    }

    def __init__(self, handler: logging.Handler) -> None:
        class_type = handler.__class__.__name__
        if class_type == "StreamHandler":
            MODIFIERS = {
                logging.TRACE: self.grey,  # logging.TRACE
                logging.DEBUG: self.blue,
                logging.INFO: self.magenta,
                logging.WARNING: self.yellow,
                logging.ERROR: self.red,
                logging.CRITICAL: self.bold_red
            }
            for key in self.FORMATS:
                message = self.FORMATS[key]
                modifider = MODIFIERS[key]
                self.FORMATS[key] = modifider + message + self.reset
        elif class_type == "FileHandler":
            pass
        else:
            raise ValueError("Logging handlertype not supporting.")

    def format(self, record):
        record.levelname_brackets = f'[{record.levelname}]'
        stack_format = f'({record.filename}:{record.funcName}:{record.lineno})'
        record.stack_format = f"{stack_format:<36s}"

        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, "%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def configure_logging() -> None:
    """Define all the configuration for logging."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.TRACE)

    # remove logging from PILLOW library
    logging.getLogger("PIL").propagate = False

    # clear crash.log
    crashlog_file = "crash.log"
    open(crashlog_file, "w", encoding="utf-8").close()

    # set logging settings
    handler = logging.StreamHandler(
        sys.stdout) if args.dev_mode else logging.FileHandler(crashlog_file)
    handler.setFormatter(CustomFormatter(handler))
    root_logger.addHandler(handler)


configure_logging()
