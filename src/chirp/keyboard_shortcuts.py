from __future__ import annotations

import logging
from typing import Callable

import keyboard


class KeyboardShortcutManager:
    def __init__(self, *, logger: logging.Logger) -> None:
        self._logger = logger

    def register(self, shortcut: str, callback: Callable[[], None]) -> None:
        try:
            keyboard.add_hotkey(shortcut, callback)
        except Exception as exc:  # pragma: no cover - runtime safety
            self._logger.error("Failed to register hotkey %s: %s", shortcut, exc)
            raise

    def send(self, combination: str) -> None:
        keyboard.send(combination)

    def write(self, text: str) -> None:
        keyboard.write(text)

    def wait(self) -> None:
        keyboard.wait()
