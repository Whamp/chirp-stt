import sys
from unittest.mock import MagicMock

# Mock sounddevice and winsound immediately
sys.modules["sounddevice"] = MagicMock()
sys.modules["winsound"] = MagicMock()
sys.modules["keyboard"] = MagicMock()

import unittest
from unittest.mock import patch
import numpy as np

# Now we can import
from chirp.main import ChirpApp

class TestChirpApp(unittest.TestCase):
    @patch("chirp.main.ParakeetManager")
    @patch("chirp.main.AudioCapture")
    @patch("chirp.main.KeyboardShortcutManager")
    @patch("chirp.main.AudioFeedback")
    @patch("chirp.main.TextInjector")
    @patch("chirp.main.ConfigManager")
    @patch("chirp.main.get_logger")
    @patch("chirp.main.RichHandler")
    @patch("chirp.main.Console")
    def test_transcription_shows_spinner(
        self,
        mock_console_cls,
        mock_rich_handler,
        mock_get_logger,
        mock_config_manager,
        mock_text_injector,
        mock_audio_feedback,
        mock_keyboard,
        mock_audio_capture,
        mock_parakeet_manager,
    ):
        # Setup mocks
        mock_console_instance = MagicMock()
        mock_console_cls.return_value = mock_console_instance

        # Mock logger
        mock_logger = MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger

        # Mock config
        mock_config = MagicMock()
        mock_config.parakeet_model = "test_model"
        mock_config.parakeet_quantization = None
        mock_config.onnx_providers = "cpu"
        mock_config.threads = 1
        mock_config.audio_feedback = False
        mock_config.model_timeout = 300
        mock_config.start_sound_path = None
        mock_config.stop_sound_path = None
        mock_config.error_sound_path = None
        mock_config.audio_feedback_volume = 1.0

        mock_config_manager_instance = mock_config_manager.return_value
        mock_config_manager_instance.load.return_value = mock_config
        mock_config_manager_instance.model_dir.return_value = "dummy_path"

        # Initialize App
        app = ChirpApp(verbose=False)

        # Mock Parakeet transcribe
        app.parakeet.transcribe.return_value = "Hello world"

        # Create a dummy waveform
        waveform = np.zeros(16000, dtype=np.float32)

        # Call _transcribe_and_inject directly
        app._transcribe_and_inject(waveform)

        # Verify status spinner was used
        status_calls = mock_console_instance.status.call_args_list
        messages = [str(call.args[0]) for call in status_calls]

        print(f"Status calls: {messages}")

        # Assertions
        # Expect "Initializing Parakeet model..." from __init__
        self.assertTrue(any("Initializing Parakeet model" in msg for msg in messages))

        # Expect "Transcribing..." from _transcribe_and_inject (THIS IS WHAT WE WANT TO ADD)
        self.assertTrue(any("Transcribing" in msg for msg in messages), "Transcribing status spinner not found")

if __name__ == "__main__":
    unittest.main()
