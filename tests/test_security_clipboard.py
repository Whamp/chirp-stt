import sys
import unittest
from unittest.mock import MagicMock, patch
from chirp.text_injector import TextInjector
from chirp.keyboard_shortcuts import KeyboardShortcutManager

class TestTextInjectorSecurity(unittest.TestCase):
    def setUp(self):
        self.keyboard = MagicMock(spec=KeyboardShortcutManager)
        self.logger = MagicMock()
        self.config = {
            "keyboard_manager": self.keyboard,
            "logger": self.logger,
            "paste_mode": "ctrl",
            "word_overrides": {},
            "post_processing": "",
            "clipboard_behavior": True,
            "clipboard_clear_delay": 0.5,
        }

    @patch("chirp.text_injector.pyperclip")
    @patch("chirp.text_injector.sys")
    @patch("chirp.text_injector.time")
    def test_inject_windows_clipboard_leak(self, mock_time, mock_sys, mock_pyperclip):
        """Test that inject() DOES NOT copy to clipboard on Windows."""
        mock_sys.platform = "win32"
        injector = TextInjector(**self.config)

        injector.inject("secret password")

        # FIXED BEHAVIOR: It should NOT copy to clipboard
        mock_pyperclip.copy.assert_not_called()
        # It should use keyboard.write
        self.keyboard.write.assert_called_with("secret password")

    @patch("chirp.text_injector.pyperclip")
    @patch("chirp.text_injector.sys")
    @patch("chirp.text_injector.time")
    def test_inject_linux_clipboard_usage(self, mock_time, mock_sys, mock_pyperclip):
        """Test that inject() uses clipboard on Linux, which is expected/required."""
        mock_sys.platform = "linux"
        injector = TextInjector(**self.config)

        injector.inject("hello world")

        # EXPECTED: Copies to clipboard
        mock_pyperclip.copy.assert_called_with("hello world")
        # And uses keyboard.send
        self.keyboard.send.assert_called_with("ctrl+v")

if __name__ == "__main__":
    unittest.main()
