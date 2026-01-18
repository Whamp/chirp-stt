import unittest
import logging
from unittest.mock import MagicMock
import sys
import os

# Add src to sys.path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from chirp.text_injector import TextInjector
from chirp.keyboard_shortcuts import KeyboardShortcutManager
from chirp.config_manager import ChirpConfig

class TestTextInjectorSecurity(unittest.TestCase):
    def setUp(self):
        self.mock_keyboard = MagicMock(spec=KeyboardShortcutManager)
        self.logger = logging.getLogger("test_logger")

        self.injector = TextInjector(
            keyboard_manager=self.mock_keyboard,
            logger=self.logger,
            paste_mode="ctrl",
            word_overrides={},
            post_processing="",
            clipboard_behavior=False,
            clipboard_clear_delay=0.1
        )

    def test_control_char_sanitization(self):
        """Verify that non-printable control characters are removed."""
        # \x07 (Bell), \x1b (Escape), \x08 (Backspace)
        # We want to keep normal text and spaces.
        dirty_text = "Hello\x07 \x1bWorld\x08!"
        processed = self.injector.process(dirty_text)

        # Expected: "Hello World!" (backspace removed, bell removed, escape removed)
        # _normalize_punctuation also runs, but it mostly handles spaces.

        # We want the output to NOT contain control chars.
        for char in processed:
            if not char.isprintable():
                self.fail(f"Found non-printable character code: {ord(char)}")

class TestConfigSecurity(unittest.TestCase):
    def test_default_recording_limit(self):
        """Verify the default recording limit is set to 45s per user request."""
        config = ChirpConfig()
        self.assertEqual(config.max_recording_duration, 45.0)

if __name__ == "__main__":
    unittest.main()
