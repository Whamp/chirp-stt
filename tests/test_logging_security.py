import logging
import unittest
from unittest.mock import MagicMock, patch
import io
import sys
import types

# Mock sounddevice globally because it's missing in the test environment
# and imported at top-level by chirp.audio_capture
if "sounddevice" not in sys.modules:
    mock_sd = types.ModuleType("sounddevice")
    mock_sd.InputStream = MagicMock()
    sys.modules["sounddevice"] = mock_sd

# Mock winsound if on Windows (but we are likely on Linux here, but just in case)
if sys.platform == "win32" and "winsound" not in sys.modules:
    mock_winsound = types.ModuleType("winsound")
    sys.modules["winsound"] = mock_winsound

from chirp.main import ChirpApp

class TestLoggingSecurity(unittest.TestCase):
    @patch("chirp.main.ParakeetManager")
    @patch("chirp.main.AudioCapture")
    @patch("chirp.main.AudioFeedback")
    @patch("chirp.main.KeyboardShortcutManager")
    @patch("chirp.main.ConfigManager")
    def test_sensitive_transcription_not_logged_at_info(self, mock_config, mock_keyboard, mock_feedback, mock_capture, mock_parakeet):
        """Verify that sensitive transcription text is NOT logged at INFO level."""
        # Setup mocks
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
        mock_config_instance.load.return_value.max_recording_duration = 45.0
        mock_config_instance.load.return_value.audio_feedback = True
        mock_config_instance.load.return_value.audio_feedback_volume = 1.0
        mock_config_instance.load.return_value.start_sound_path = None
        mock_config_instance.load.return_value.stop_sound_path = None
        mock_config_instance.load.return_value.model_timeout = 300.0
        mock_config_instance.model_dir.return_value = "models/test-model"

        # Capture logs
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.INFO)

        # Configure the chirp logger
        logger = logging.getLogger("chirp")
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Initialize app
        app = ChirpApp()

        # Simulate transcription
        sensitive_text = "My secret password is hunter2"
        app.parakeet.transcribe.return_value = sensitive_text

        # Simulate stop recording which triggers transcribe
        import numpy as np
        waveform = np.zeros(16000)
        app._transcribe_and_inject(waveform)

        # Check logs
        log_contents = log_capture.getvalue()

        # Assert that sensitive text is NOT in the logs
        self.assertNotIn(sensitive_text, log_contents, "Sensitive transcription text leaked into INFO logs!")

        # Verify that it IS logged if we enable DEBUG (optional, to verify it's not lost completely)
        # But we can't easily change logger level mid-run and re-capture without clearing, so we skip that for now.
        # The important part is security.

if __name__ == "__main__":
    unittest.main()
