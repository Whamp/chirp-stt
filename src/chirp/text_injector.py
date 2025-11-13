from __future__ import annotations

import logging
import re
import sys
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional

import pyperclip

from .keyboard_shortcuts import KeyboardShortcutManager


@dataclass(slots=True)
class StyleGuide:
    sentence_case: bool = False
    uppercase: bool = False
    lowercase: bool = False
    prepend: str = ""
    append: str = ""

    @classmethod
    def from_prompt(cls, prompt: str) -> "StyleGuide":
        guide = cls()
        for raw_line in prompt.splitlines():
            line = raw_line.strip()
            lower = line.lower()
            if not line:
                continue
            if lower in {"sentence case", "sentence-case", "capitalize sentences"}:
                guide.sentence_case = True
            elif lower in {"uppercase", "upper"}:
                guide.uppercase = True
                guide.sentence_case = False
                guide.lowercase = False
            elif lower in {"lowercase", "lower"}:
                guide.lowercase = True
                guide.uppercase = False
                guide.sentence_case = False
            elif lower.startswith("prepend:"):
                guide.prepend = line.partition(":")[2].strip()
            elif lower.startswith("append:"):
                guide.append = line.partition(":")[2].strip()
        return guide

    def apply(self, text: str) -> str:
        result = text
        if self.uppercase:
            result = result.upper()
        elif self.lowercase:
            result = result.lower()
        elif self.sentence_case:
            result = _sentence_case(result)
        if self.prepend:
            result = f"{self.prepend} {result}".strip()
        if self.append:
            result = f"{result} {self.append}".strip()
        return result


class TextInjector:
    def __init__(
        self,
        *,
        keyboard_manager: KeyboardShortcutManager,
        logger: logging.Logger,
        paste_mode: str,
        word_overrides: Dict[str, str],
        whisper_prompt: str,
        clipboard_behavior: bool,
        clipboard_clear_delay: float,
    ) -> None:
        self._keyboard = keyboard_manager
        self._logger = logger
        self._paste_mode = paste_mode
        self._word_overrides = {k.lower(): v for k, v in word_overrides.items()}
        self._override_pattern = self._build_override_pattern(self._word_overrides)
        self._style = StyleGuide.from_prompt(whisper_prompt)
        self._clipboard_behavior = clipboard_behavior
        self._clipboard_clear_delay = max(0.1, clipboard_clear_delay)

    def process(self, text: str) -> str:
        result = text.strip()
        if not result:
            return result
        result = self._apply_word_overrides(result)
        result = _normalize_punctuation(result)
        result = self._style.apply(result)
        return result

    def inject(self, text: str) -> None:
        processed = self.process(text)
        try:
            pyperclip.copy(processed)
        except pyperclip.PyperclipException as exc:  # pragma: no cover - clipboard edge cases
            self._logger.error("Clipboard copy failed: %s", exc)
            return
        time.sleep(0.12)
        try:
            if sys.platform.startswith("win"):
                self._keyboard.write(processed)
            else:
                combo = "ctrl+v" if self._paste_mode == "ctrl" else "ctrl+shift+v"
                self._keyboard.send(combo)
        except Exception as exc:  # pragma: no cover - runtime safety
            self._logger.error("Paste injection failed: %s", exc)
        if self._clipboard_behavior:
            self._schedule_clipboard_clear()

    def _schedule_clipboard_clear(self) -> None:
        def _clear() -> None:
            try:
                pyperclip.copy("")
            except pyperclip.PyperclipException:
                pass

        timer = threading.Timer(self._clipboard_clear_delay, _clear)
        timer.daemon = True
        timer.start()

    def _apply_word_overrides(self, text: str) -> str:
        if not self._override_pattern:
            return text

        def _replace(match: re.Match[str]) -> str:
            return self._word_overrides.get(match.group(0).lower(), match.group(0))

        return self._override_pattern.sub(_replace, text)

    @staticmethod
    def _build_override_pattern(overrides: Dict[str, str]) -> Optional[re.Pattern[str]]:
        if not overrides:
            return None
        escaped = sorted((re.escape(word) for word in overrides.keys()), key=len, reverse=True)
        pattern = r"\b(" + "|".join(escaped) + r")\b"
        return re.compile(pattern, flags=re.IGNORECASE)


def _normalize_punctuation(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;!?])", r"\1", text)
    text = text.replace(" ,", ",").replace(" .", ".")
    return text.strip()


def _sentence_case(text: str) -> str:
    result = []
    capitalize_next = True
    for ch in text:
        if capitalize_next and ch.isalpha():
            result.append(ch.upper())
            capitalize_next = False
        else:
            result.append(ch.lower())
        if ch in ".!?\n":
            capitalize_next = True
    return "".join(result)
