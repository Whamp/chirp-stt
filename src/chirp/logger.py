from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler


def get_logger(name: str = "chirp", *, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        logger.setLevel(level)
        for handler in logger.handlers:
            handler.setLevel(level)
        return logger
    console = Console(force_terminal=True)
    handler = RichHandler(console=console, show_time=True, markup=False)
    handler.setLevel(level)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


def configure_root(level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, handlers=[RichHandler(console=Console(force_terminal=True))])
