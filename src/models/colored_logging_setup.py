# Python
import logging
import sys
from colorama import init, Fore, Style

init(autoreset=True)


class ColorFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: Fore.BLUE,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        levelname = f"{color}{record.levelname}{Style.RESET_ALL}"
        record.levelname = levelname
        return super().format(record)


def setup_colored_logging(level=logging.INFO):
    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handler.setFormatter(ColorFormatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

# setup_colored_logging(logging.DEBUG)
# logger = logging.getLogger(__name__)
# logger.info("Hello colored world")
