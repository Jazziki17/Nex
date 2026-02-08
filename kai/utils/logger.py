"""
Logging Utility
================

LEARNING POINT: Why Logging Matters
-------------------------------------
Never use `print()` in production code. Use logging instead because:

1. **Log Levels** — You can filter by severity (DEBUG, INFO, WARNING, ERROR)
   - DEBUG:   Detailed info for diagnosing problems
   - INFO:    Confirmation things are working
   - WARNING: Something unexpected but not broken
   - ERROR:   Something failed

2. **Output Control** — Send logs to console, files, or external services
   without changing your code

3. **Context** — Logs automatically include timestamps, module names,
   and line numbers

4. **Performance** — Logging can be disabled in production without
   removing log statements from code

EXAMPLE:
    from kai.utils.logger import setup_logger

    logger = setup_logger(__name__)

    logger.debug("Processing audio chunk #42")      # Only in debug mode
    logger.info("Voice module started")              # Normal operations
    logger.warning("Microphone quality is low")      # Potential issues
    logger.error("Failed to open camera")            # Actual failures
"""

import logging
import sys
from pathlib import Path


# LEARNING POINT: Module-level constant
# Define the log format once, use it everywhere. The format string uses
# special %-style placeholders that the logging module understands:
#   %(asctime)s    — timestamp
#   %(name)s       — logger name (usually the module)
#   %(levelname)s  — DEBUG/INFO/WARNING/ERROR
#   %(message)s    — the actual log message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
DATE_FORMAT = "%H:%M:%S"


def setup_logger(
    name: str,
    level: int = logging.DEBUG,
    log_file: str | None = None,
) -> logging.Logger:
    """
    Create and configure a logger instance.

    LEARNING POINT: Factory Function
    ----------------------------------
    This is a "factory" — a function that creates and returns configured
    objects. Instead of repeating logger setup code everywhere, you call
    this once per module.

    Args:
        name: Logger name (typically __name__ of the calling module)
        level: Minimum log level to capture
        log_file: Optional file path to also write logs to

    Returns:
        A configured Logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Console handler — prints to terminal with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColorFormatter(LOG_FORMAT, DATE_FORMAT))
    logger.addHandler(console_handler)

    # File handler — writes to a log file (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        logger.addHandler(file_handler)

    return logger


class ColorFormatter(logging.Formatter):
    """
    Custom formatter that adds color to terminal output.

    LEARNING POINT: ANSI Escape Codes
    ------------------------------------
    Terminals support special character sequences to change text color.
    These are called ANSI escape codes. The format is:
        \\033[<code>m   — start color
        \\033[0m        — reset to default

    This is purely cosmetic but makes logs MUCH easier to read in a
    terminal. Colors are only added to console output, not file output.
    """

    COLORS = {
        logging.DEBUG:    "\033[36m",    # Cyan
        logging.INFO:     "\033[32m",    # Green
        logging.WARNING:  "\033[33m",    # Yellow
        logging.ERROR:    "\033[31m",    # Red
        logging.CRITICAL: "\033[1;31m",  # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)
