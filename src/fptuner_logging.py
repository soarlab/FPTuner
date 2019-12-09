

import color_printing

import inspect
import sys
import os.path as path



class Logger():
    # Constants
    NONE = -10
    QUIET = 0
    LOW = 10
    MEDIUM = 20
    HIGH = 30

    # Class variables
    LOG_LEVEL = LOW
    LOG_FILE = sys.stdout
    LOGGER_COUNT = 0

    def __init__(self, color=None, level=None):
        if color is None:
            self.color = color_printing.cyan
        else:
            self.color = color

        if level is None:
           self.level = Logger.LOW
        else:
            self.level = level

        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        filename = module.__file__
        base = path.basename(filename)
        self.module = path.splitext(base)[0]

        Logger.LOGGER_COUNT += 1

    def __del__(self):
        Logger.LOGGER_COUNT -= 1
        if Logger.LOGGER_COUNT == 0 and Logger.LOG_FILE != sys.stdout:
            Logger.LOG_FILE.close()
            Logger.LOG_FILE = None

    def set_log_level(self, level):
        Logger.LOG_LEVEL = level

    def set_log_filename(self, filename):
        Logger.LOG_FILE = open(filename, "w")

    def should_log(self, level=None):
        if level is None:
            return self.level <= Logger.LOG_LEVEL
        return level <= Logger.LOG_LEVEL

    def _log(self, formatted_message, pre=None, out=None):
        if pre is None:
            pre = ""

        mod = self.color(self.module)
        full_message = "{}:{} {}".format(mod, pre, formatted_message)
        if Logger.LOG_FILE != sys.stdout:
            full_message = color_printing.strip(full_message)
        if out is None:
            print(full_message, file=Logger.LOG_FILE)
        else:
            print(full_message, file=out)
        return full_message

    def log(self, message, *args):
        if self.level <= Logger.LOG_LEVEL:
            formatted_message = message.format(*args)
            self._log(formatted_message)

    def llog(self, level, message, *args):
        if level <= Logger.LOG_LEVEL:
            formatted_message = message.format(*args)
            self._log(formatted_message)

    def dlog(self, message, *args):
        if self.level <= Logger.LOG_LEVEL:
            frame = inspect.stack()[1]
            funcname = color_printing.magenta(frame.function)
            formatted_message = message.format(*args)
            self._log(formatted_message, pre=funcname+":")

    def warning(self, message, *args):
        if Logger.LOG_LEVEL >= Logger.NONE:
            warn = color_printing.yellow("WARNING") + ":"
            formatted_message = message.format(*args)
            full_message = self._log(formatted_message, warn, sys.stderr)
            if Logger.LOG_FILE != sys.stdout:
                print(color.strip(full_message), file=Logger.LOG_FILE)

    def error(self, message, *args):
        err = color_printing.red("ERROR") + ":"
        formatted_message = message.format(*args)
        full_message = self._log(formatted_message, err, sys.stderr)
        if Logger.LOG_FILE != sys.stdout:
            print(color.strip(full_message), file=Logger.LOG_FILE)



