import sys
import unittest
from unittest.mock import MagicMock, patch, call

# Mock dependencies before import
sys.modules["sounddevice"] = MagicMock()
sys.modules["keyboard"] = MagicMock()

# Now we can import chirp.main
from chirp.main import ChirpApp
from rich.logging import RichHandler

class TestUIStatus(unittest.TestCase):
    @patch("chirp.main.ConfigManager")
    @patch("chirp.main.get_logger")
    @patch("chirp.main.ParakeetManager")
    @patch("chirp.main.AudioCapture")
    @patch("chirp.main.AudioFeedback")
    @patch("chirp.main.TextInjector")
    def test_status_indicator_lifecycle(
        self,
        MockTextInjector,
        MockAudioFeedback,
        MockAudioCapture,
        MockParakeetManager,
        MockGetLogger,
        MockConfigManager,
    ):
        # Setup mocks
        mock_logger = MagicMock()
        mock_console = MagicMock()

        # Configure console.status to return different mocks for different calls if needed,
        # or just reuse the same one. For simplicity, let's reuse, but distinct calls matter.
        # Let's verify calls were made.

        handler = RichHandler(console=mock_console)
        mock_logger.handlers = [handler]

        MockGetLogger.return_value = mock_logger

        # Setup Config
        mock_config = MockConfigManager.return_value.load.return_value
        mock_config.parakeet_model = "test-model"
        mock_config.parakeet_quantization = None
        mock_config.onnx_providers = "cpu"
        mock_config.threads = 1
        mock_config.audio_feedback = False
        mock_config.max_recording_duration = 0
        mock_config.model_timeout = 300
        mock_config.paste_mode = "ctrl"
        mock_config.word_overrides = {}
        mock_config.post_processing = ""
        mock_config.clipboard_behavior = False
        mock_config.clipboard_clear_delay = 0.5
        mock_config.start_sound_path = ""
        mock_config.stop_sound_path = ""
        mock_config.error_sound_path = ""
        mock_config.primary_shortcut = "ctrl+space"
        mock_config.language = "en"

        app = ChirpApp()

        # Verify initialization
        self.assertEqual(app.console, mock_console)

        # Verify "Ready" status was requested
        # We expect a call to status("Ready")
        mock_console.status.assert_any_call("Ready")

        status_mock = app.status_indicator

        # Test Start Recording
        app._start_recording()
        status_mock.update.assert_called_with("[bold red]Recording...[/bold red]", spinner="point")
        status_mock.start.assert_called()

        # Test Stop Recording
        app._stop_recording()
        status_mock.update.assert_called_with("[bold green]Transcribing...[/bold green]", spinner="dots")

        # Test Transcribe (simulate thread execution)
        waveform = MagicMock()
        waveform.size = 100

        # Case 1: finish transcription and not recording
        app._recording = False
        app._transcribe_and_inject(waveform)
        status_mock.stop.assert_called()

        # Reset mocks
        status_mock.stop.reset_mock()

        # Case 2: finish transcription but recording started again
        app._recording = True
        app._transcribe_and_inject(waveform)
        status_mock.stop.assert_not_called()

if __name__ == "__main__":
    unittest.main()
