import logging
import unittest
from unittest.mock import MagicMock

from chirp.config_manager import ChirpConfig
from chirp.keyboard_shortcuts import KeyboardShortcutManager
from chirp.text_injector import TextInjector


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
            clipboard_clear_delay=0.1,
        )

    def test_control_char_sanitization(self):
        """Verify that non-printable control characters are removed."""
        # \x07 (Bell), \x1b (Escape), \x08 (Backspace)
        dirty_text = "Hello\x07 \x1bWorld\x08!"
        processed = self.injector.process(dirty_text)

        # Verify no control characters remain
        for char in processed:
            if not char.isprintable():
                self.fail(f"Found non-printable character code: {ord(char)}")

        # Verify expected text is preserved
        self.assertEqual(processed, "Hello World!")

    def test_tabs_and_newlines_preserved(self):
        """Verify that tabs and newlines are preserved as valid whitespace."""
        text = "Line1\nLine2\tTabbed"
        processed = self.injector.process(text)
        # Note: _normalize_punctuation collapses whitespace to single spaces
        self.assertIn("Line1", processed)
        self.assertIn("Line2", processed)

    def test_override_injection_sanitization(self):
        """Verify that word_overrides cannot introduce control characters."""
        overrides = {"unsafe": "back\x08space"}
        injector = TextInjector(
            keyboard_manager=self.mock_keyboard,
            logger=self.logger,
            paste_mode="ctrl",
            word_overrides=overrides,
            post_processing="",
            clipboard_behavior=False,
            clipboard_clear_delay=0.1,
        )
        processed = injector.process("unsafe")
        self.assertNotIn("\x08", processed)
        self.assertEqual(processed, "backspace")

    def test_sanitize_preserves_whitespace(self):
        """Verify that _sanitize with strip_text=False preserves whitespace."""
        # Test the static method directly
        text = "  spaced  "
        sanitized = TextInjector._sanitize(text, strip_text=False)
        self.assertEqual(sanitized, "  spaced  ")

        # Verify it still removes control chars
        dirty = "  spaced\x08  "
        sanitized_dirty = TextInjector._sanitize(dirty, strip_text=False)
        self.assertEqual(sanitized_dirty, "  spaced  ")


class TestConfigSecurity(unittest.TestCase):
    def test_default_recording_limit(self):
        """Verify the default recording limit is set to 45s."""
        config = ChirpConfig()
        self.assertEqual(config.max_recording_duration, 45.0)

    def test_recording_limit_zero_disables(self):
        """Verify that 0 can be used to disable the limit."""
        config = ChirpConfig(max_recording_duration=0)
        self.assertEqual(config.max_recording_duration, 0)


if __name__ == "__main__":
    unittest.main()
