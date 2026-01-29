import unittest
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Mock dependencies that require C libs or hardware access
mock_sd = MagicMock()
sys.modules["sounddevice"] = mock_sd
mock_keyboard = MagicMock()
sys.modules["keyboard"] = mock_keyboard
mock_winsound = MagicMock()
sys.modules["winsound"] = mock_winsound
mock_pyperclip = MagicMock()
sys.modules["pyperclip"] = mock_pyperclip

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

import numpy as np  # noqa: E402
from chirp.main import ChirpApp  # noqa: E402

class TestChirpAppStatus(unittest.TestCase):
    @patch('chirp.main.TextInjector')
    @patch('chirp.main.KeyboardShortcutManager')
    @patch('chirp.main.AudioFeedback')
    @patch('chirp.main.AudioCapture')
    @patch('chirp.main.ParakeetManager')
    @patch('chirp.main.ConfigManager')
    @patch('chirp.main.RichHandler')
    @patch('chirp.main.get_logger')
    def test_transcription_shows_status(
        self,
        mock_get_logger,
        mock_rich_handler_cls,
        mock_config_manager,
        mock_parakeet_cls,
        mock_audio_capture,
        mock_audio_feedback,
        mock_keyboard,
        mock_text_injector
    ):
        with patch('chirp.main.Console') as MockConsole:
            # Force fallback to new Console creation
            mock_logger = MagicMock()
            mock_logger.handlers = []
            mock_get_logger.return_value = mock_logger

            app = ChirpApp()

            mock_console_instance = MockConsole.return_value

            # Reset mocks
            mock_console_instance.reset_mock()

            # Run transcribe
            waveform = np.zeros(1024, dtype=np.float32)
            app.parakeet.transcribe.return_value = "Test text"

            app._transcribe_and_inject(waveform)

            # Verify status was called with Transcribing...
            mock_console_instance.status.assert_called_with("[bold yellow]Transcribing...[/bold yellow]", spinner="dots")

if __name__ == "__main__":
    unittest.main()
