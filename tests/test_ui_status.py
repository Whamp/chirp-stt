import sys
from unittest.mock import MagicMock

# Mock sounddevice before importing chirp.main because it fails on import if PortAudio is missing
sys.modules["sounddevice"] = MagicMock()
sys.modules["winsound"] = MagicMock()

import logging  # noqa: E402
import unittest  # noqa: E402
from unittest.mock import patch  # noqa: E402
from rich.logging import RichHandler  # noqa: E402

from chirp.main import ChirpApp  # noqa: E402


class TestChirpAppUI(unittest.TestCase):
    @patch("chirp.main.get_logger")
    @patch("chirp.main.ConfigManager")
    @patch("chirp.main.KeyboardShortcutManager")
    @patch("chirp.main.AudioCapture")
    @patch("chirp.main.AudioFeedback")
    @patch("chirp.main.ParakeetManager")
    @patch("chirp.main.TextInjector")
    @patch("chirp.main.Console")
    # Removed RichHandler patch
    def setUp(self, mock_console, mock_text_injector, mock_parakeet,
              mock_audio_feedback, mock_audio_capture, mock_keyboard, mock_config, mock_get_logger):

        # Setup mocks
        self.mock_logger = MagicMock(spec=logging.Logger)
        self.mock_logger.handlers = []
        mock_get_logger.return_value = self.mock_logger

        # Mock Config
        mock_config_instance = mock_config.return_value
        mock_config_instance.load.return_value = MagicMock(
            parakeet_model="test-model",
            parakeet_quantization=None,
            onnx_providers="cpu",
            threads=0,
            paste_mode="ctrl",
            audio_feedback=False,
            word_overrides={},
            post_processing="",
            clipboard_behavior=False,
            clipboard_clear_delay=0.0,
            max_recording_duration=0,
            error_sound_path="",
            start_sound_path="",
            stop_sound_path="",
            language="en"
        )

        # Mock Console and Status
        self.mock_console_instance = mock_console.return_value
        self.mock_status = MagicMock()
        self.mock_console_instance.status.return_value = self.mock_status

        # Setup logger handlers to include a real RichHandler with our mock console
        # We need to construct it carefully or just mock the isinstance check?
        # Creating a real RichHandler requires a Console.
        # We can pass our mock console to it.
        real_handler = RichHandler(console=self.mock_console_instance)
        self.mock_logger.handlers = [real_handler]

        self.app = ChirpApp()

        # Manually attach the status indicator since we haven't implemented it in __init__ yet.
        self.app.status_indicator = self.mock_status

    def test_init_creates_status(self):
        # This test verifies that status was called during init
        self.mock_console_instance.status.assert_called_with("[bold green]Initializing Parakeet model...[/bold green]", spinner="dots")

    def test_start_recording_updates_status(self):
        self.app._start_recording()
        self.mock_status.update.assert_called_with("Recording...", spinner="dots")
        self.mock_status.start.assert_called_once()

    def test_stop_recording_updates_status(self):
        self.app._recording = True
        self.app._executor = MagicMock()
        self.app._stop_recording()
        self.mock_status.update.assert_called_with("Transcribing...", spinner="dots")

    def test_transcribe_stops_status_when_done(self):
        waveform = MagicMock()
        waveform.size = 100

        self.app.parakeet = MagicMock()
        self.app.parakeet.transcribe.return_value = "test"

        self.app._recording = False
        self.app._transcribe_and_inject(waveform)
        self.mock_status.stop.assert_called_once()

    def test_transcribe_does_not_stop_status_if_recording(self):
        waveform = MagicMock()
        waveform.size = 100

        self.app.parakeet = MagicMock()
        self.app.parakeet.transcribe.return_value = "test"

        self.app._recording = True
        self.app._transcribe_and_inject(waveform)
        self.mock_status.stop.assert_not_called()
