import sys
import unittest
from unittest.mock import MagicMock, patch
import types
import numpy as np

# Mock dependencies that are not available in the test environment
if "sounddevice" not in sys.modules:
    mock_sd = types.ModuleType("sounddevice")
    mock_sd.InputStream = MagicMock()
    sys.modules["sounddevice"] = mock_sd

if "winsound" not in sys.modules:
    mock_winsound = types.ModuleType("winsound")
    sys.modules["winsound"] = mock_winsound

from chirp.main import ChirpApp

class TestChirpUI(unittest.TestCase):
    @patch("chirp.main.ParakeetManager")
    @patch("chirp.main.AudioCapture")
    @patch("chirp.main.AudioFeedback")
    @patch("chirp.main.KeyboardShortcutManager")
    @patch("chirp.main.ConfigManager")
    def test_transcription_status_indicator(self, mock_config, mock_keyboard, mock_feedback, mock_capture, mock_parakeet):
        """Verify that the 'Transcribing...' status is shown during transcription."""

        # Setup mock config
        mock_config_instance = mock_config.return_value
        mock_config_instance.load.return_value.parakeet_model = "test-model"
        mock_config_instance.load.return_value.parakeet_quantization = None
        mock_config_instance.load.return_value.onnx_providers = "cpu"
        mock_config_instance.load.return_value.threads = 1
        mock_config_instance.load.return_value.paste_mode = "ctrl"
        mock_config_instance.load.return_value.word_overrides = {}
        mock_config_instance.load.return_value.post_processing = ""
        mock_config_instance.load.return_value.clipboard_behavior = False
        mock_config_instance.load.return_value.clipboard_clear_delay = 1.0
        mock_config_instance.load.return_value.max_recording_duration = 0
        mock_config_instance.load.return_value.audio_feedback = False
        mock_config_instance.load.return_value.model_timeout = 300.0
        mock_config_instance.model_dir.return_value = "models/test-model"

        # Mock ParakeetManager transcription
        mock_parakeet_instance = mock_parakeet.return_value
        mock_parakeet_instance.transcribe.return_value = "Test transcription"

        # Mock Console and Status
        mock_console = MagicMock()
        mock_status = MagicMock()
        mock_console.status.return_value.__enter__.return_value = mock_status

        # We need to ensure that when ChirpApp is initialized, it uses our mock console.
        # Since ChirpApp looks for RichHandler in logger.handlers, we can patch `get_logger`
        # OR we can patch `Console` if ChirpApp creates a new one.
        # However, ChirpApp logic is:
        #   if RichHandler in logger.handlers -> use its console
        #   else -> create new Console(stderr=True)
        #
        # Easier path: Patch Console globally, and ensure get_logger returns a logger without RichHandler.

        with patch("chirp.main.get_logger") as mock_get_logger, \
             patch("chirp.main.Console", return_value=mock_console) as mock_console_class:

            # Setup logger mock to have no handlers so it falls back to creating a new Console
            mock_logger = MagicMock()
            mock_logger.handlers = []
            mock_get_logger.return_value = mock_logger

            # Initialize App
            app = ChirpApp()

            # Trigger transcription
            waveform = np.zeros(16000)
            app._transcribe_and_inject(waveform)

            # Verify status was called with "Transcribing..."
            # Note: app._transcribe_and_inject calls app.parakeet.transcribe
            # We want to check that console.status("Transcribing...", spinner="dots") was entered.

            status_calls = mock_console.status.call_args_list
            transcribing_called = False
            for args, kwargs in status_calls:
                if "Transcribing..." in args[0] and kwargs.get("spinner") == "dots":
                    transcribing_called = True
                    break

            self.assertTrue(transcribing_called, "Console status 'Transcribing...' was not triggered.")

if __name__ == "__main__":
    unittest.main()
