"""Logging config for the Husqvarna Automower API."""

import logging

from colorlog import ColoredFormatter

FORMAT_DATE = "%Y-%m-%d"
FORMAT_TIME = "%H:%M:%S"
FORMAT_DATETIME = f"{FORMAT_DATE} {FORMAT_TIME}"
fmt = "%(asctime)s.%(msecs)03d %(levelname)s (%(threadName)s) [%(name)s] %(message)s"


def setup_logging(level: int = logging.DEBUG) -> None:
    """Set up global logger."""
    handler = logging.StreamHandler()
    formatter = ColoredFormatter(
        f"%(log_color)s{fmt}%(reset)s",
        datefmt=FORMAT_DATETIME,
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red",
        },
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    if not root_logger.handlers:
        root_logger.addHandler(handler)
