import unittest
import logging
from unittest.mock import MagicMock
import sys
import os

# Add src to sys.path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from chirp.text_injector import TextInjector
from chirp.keyboard_shortcuts import KeyboardShortcutManager

class TestTextInjectorSecurity(unittest.TestCase):
    def setUp(self):
        self.mock_keyboard = MagicMock(spec=KeyboardShortcutManager)
        self.logger = logging.getLogger("test_logger")
        # self.logger.addHandler(logging.StreamHandler()) # debug

        self.injector = TextInjector(
            keyboard_manager=self.mock_keyboard,
            logger=self.logger,
            paste_mode="ctrl",
            word_overrides={},
            post_processing="",
            clipboard_behavior=False,
            clipboard_clear_delay=0.1
        )

    def test_dos_prevention_length_limit(self):
        """Verify that excessively long inputs are truncated."""
        # Generates 5000 characters.
        # We expect a limit (e.g., 2000) to be enforced.
        long_text = "A" * 5000
        processed = self.injector.process(long_text)

        # This assertion is expected to FAIL before the fix
        self.assertLessEqual(len(processed), 2000, "Text was not truncated to safe limit")

    def test_control_char_sanitization(self):
        """Verify that non-printable control characters are removed."""
        # \x07 (Bell), \x1b (Escape), \x08 (Backspace)
        # We want to keep normal text and spaces.
        dirty_text = "Hello\x07 \x1bWorld\x08!"
        processed = self.injector.process(dirty_text)

        # Expected: "Hello World!" (backspace removed, bell removed, escape removed)
        # Note: _normalize_punctuation collapses spaces, so "Hello World!"
        # But if \x08 is removed, it becomes "HelloWorld!"?
        # Wait, if I simply filter non-printables:
        # "Hello" + " " + "World" + "!" -> "Hello World!"

        # Let's see what happens currently.
        # \x07 is not whitespace. \x08 is not whitespace.
        # current _normalize_punctuation regex: \s+ -> " "
        # It replaces whitespace. It does NOT touch other chars.
        # So "Hello\x07 \x1bWorld\x08!" remains mostly intact (space might be collapsed if surrounded by space)

        # We want the output to NOT contain control chars.
        for char in processed:
            if not char.isprintable():
                self.fail(f"Found non-printable character code: {ord(char)}")

if __name__ == "__main__":
    unittest.main()
