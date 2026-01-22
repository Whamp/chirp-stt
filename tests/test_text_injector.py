import sys
import unittest
from unittest.mock import MagicMock, patch
import logging

# Mock external dependencies before importing chirp modules
sys.modules["pyperclip"] = MagicMock()
sys.modules["keyboard"] = MagicMock()
sys.modules["sounddevice"] = MagicMock()

# Import the module under test
from chirp.text_injector import TextInjector  # noqa: E402
from chirp.keyboard_shortcuts import KeyboardShortcutManager  # noqa: E402

class TestTextInjector(unittest.TestCase):
    def setUp(self):
        self.mock_keyboard = MagicMock(spec=KeyboardShortcutManager)
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.injector = TextInjector(
            keyboard_manager=self.mock_keyboard,
            logger=self.mock_logger,
            paste_mode="ctrl",
            word_overrides={},
            post_processing="",
            clipboard_behavior=True,
            clipboard_clear_delay=0.1
        )

    def test_inject_windows_does_not_copy_to_clipboard(self):
        # Mock sys.platform to be win32
        with patch("sys.platform", "win32"):
            # Reset mocks
            sys.modules["pyperclip"].copy.reset_mock()
            self.mock_keyboard.write.reset_mock()

            # Call inject
            self.injector.inject("test text")

            # Assertions
            # On Windows, we should use keyboard.write
            self.mock_keyboard.write.assert_called_with("test text")

            # CRITICAL: We should NOT copy to clipboard on Windows if we are just typing
            # This is the vulnerability/issue we are fixing.
            # Currently this assertion should FAIL.
            sys.modules["pyperclip"].copy.assert_not_called()

    def test_inject_linux_copies_to_clipboard(self):
        # Mock sys.platform to be linux
        with patch("sys.platform", "linux"):
             # Reset mocks
            sys.modules["pyperclip"].copy.reset_mock()
            self.mock_keyboard.send.reset_mock()

            self.injector.inject("test text")

            # On Linux, we SHOULD copy to clipboard
            sys.modules["pyperclip"].copy.assert_called_with("test text")
            self.mock_keyboard.send.assert_called()

if __name__ == "__main__":
    unittest.main()
