import logging
import unittest
from unittest.mock import MagicMock, patch


class TestTextInjector(unittest.TestCase):
    def setUp(self):
        self.mock_keyboard = MagicMock()
        self.mock_logger = MagicMock(spec=logging.Logger)

    def _create_injector(self, paste_mode="ctrl"):
        """Create injector with mocked dependencies."""
        # Import here to ensure patches are active
        from chirp.text_injector import TextInjector

        return TextInjector(
            keyboard_manager=self.mock_keyboard,
            logger=self.mock_logger,
            paste_mode=paste_mode,
            word_overrides={},
            post_processing="",
            clipboard_behavior=False,
            clipboard_clear_delay=0.1,
        )

    @patch("chirp.text_injector.pyperclip")
    def test_inject_windows_does_not_copy_to_clipboard(self, mock_pyperclip):
        """On Windows, inject should type directly without touching clipboard."""
        with patch("chirp.text_injector.sys.platform", "win32"):
            injector = self._create_injector()
            injector.inject("test text")

            # Should use keyboard.write for direct typing
            self.mock_keyboard.write.assert_called_with("test text")

            # Should NOT touch clipboard
            mock_pyperclip.copy.assert_not_called()

    @patch("chirp.text_injector.pyperclip")
    def test_inject_linux_copies_to_clipboard(self, mock_pyperclip):
        """On Linux, inject should copy to clipboard and send paste keystroke."""
        with patch("chirp.text_injector.sys.platform", "linux"):
            injector = self._create_injector()
            injector.inject("test text")

            # Should copy to clipboard
            mock_pyperclip.copy.assert_called_with("test text")

            # Should send paste keystroke
            self.mock_keyboard.send.assert_called_with("ctrl+v")

    @patch("chirp.text_injector.pyperclip")
    def test_inject_linux_uses_ctrl_shift_v(self, mock_pyperclip):
        """On Linux with paste_mode='ctrl+shift', should use Ctrl+Shift+V."""
        with patch("chirp.text_injector.sys.platform", "linux"):
            injector = self._create_injector(paste_mode="ctrl+shift")
            injector.inject("test text")

            self.mock_keyboard.send.assert_called_with("ctrl+shift+v")


if __name__ == "__main__":
    unittest.main()
