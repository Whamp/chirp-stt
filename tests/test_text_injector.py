import logging
import sys
import time
import unittest
from unittest.mock import MagicMock, patch

# Mock external dependencies before importing chirp modules
sys.modules["pyperclip"] = MagicMock()
sys.modules["keyboard"] = MagicMock()
sys.modules["sounddevice"] = MagicMock()

from chirp.text_injector import TextInjector  # noqa: E402
from chirp.keyboard_shortcuts import KeyboardShortcutManager  # noqa: E402


class TestTextInjector(unittest.TestCase):
    def setUp(self):
        self.mock_keyboard = MagicMock(spec=KeyboardShortcutManager)
        self.mock_logger = MagicMock(spec=logging.Logger)
        # Disable clipboard_behavior to avoid timer interference between tests
        self.injector = TextInjector(
            keyboard_manager=self.mock_keyboard,
            logger=self.mock_logger,
            paste_mode="ctrl",
            word_overrides={},
            post_processing="",
            clipboard_behavior=False,
            clipboard_clear_delay=0.1,
        )
        # Reset mocks before each test
        sys.modules["pyperclip"].copy.reset_mock()
        self.mock_keyboard.reset_mock()

    def test_inject_windows_does_not_copy_to_clipboard(self):
        """On Windows, inject should type directly without touching clipboard."""
        with patch("sys.platform", "win32"):
            self.injector.inject("test text")

            # Should use keyboard.write for direct typing
            self.mock_keyboard.write.assert_called_with("test text")

            # Should NOT touch clipboard
            sys.modules["pyperclip"].copy.assert_not_called()

    def test_inject_linux_copies_to_clipboard(self):
        """On Linux, inject should copy to clipboard and send paste keystroke."""
        with patch("sys.platform", "linux"):
            self.injector.inject("test text")

            # Should copy to clipboard
            sys.modules["pyperclip"].copy.assert_called_with("test text")

            # Should send paste keystroke
            self.mock_keyboard.send.assert_called_with("ctrl+v")

    def test_inject_linux_uses_ctrl_shift_v(self):
        """On Linux with paste_mode='ctrl+shift', should use Ctrl+Shift+V."""
        injector = TextInjector(
            keyboard_manager=self.mock_keyboard,
            logger=self.mock_logger,
            paste_mode="ctrl+shift",
            word_overrides={},
            post_processing="",
            clipboard_behavior=False,
            clipboard_clear_delay=0.1,
        )
        self.mock_keyboard.reset_mock()

        with patch("sys.platform", "linux"):
            injector.inject("test text")
            self.mock_keyboard.send.assert_called_with("ctrl+shift+v")


if __name__ == "__main__":
    unittest.main()
