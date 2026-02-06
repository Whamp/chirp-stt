import unittest
from unittest.mock import MagicMock, patch
import sys
import types
import numpy as np
import time

# Mock dependencies not available in the test environment
if "sounddevice" not in sys.modules:
    mock_sd = types.ModuleType("sounddevice")
    mock_sd.InputStream = MagicMock()
    sys.modules["sounddevice"] = mock_sd

if sys.platform == "win32" and "winsound" not in sys.modules:
    mock_winsound = types.ModuleType("winsound")
    sys.modules["winsound"] = mock_winsound

# Import after mocking
from chirp.main import ChirpApp

class TestUIUX(unittest.TestCase):
    @patch("chirp.main.ParakeetManager")
    @patch("chirp.main.AudioCapture")
    @patch("chirp.main.AudioFeedback")
    @patch("chirp.main.KeyboardShortcutManager")
    @patch("chirp.main.ConfigManager")
    def test_status_indicator_updates(self, mock_config, mock_keyboard, mock_feedback, mock_capture, mock_parakeet):
        """Verify that the status indicator updates during the recording lifecycle."""
        # Setup mocks
        mock_config_instance = mock_config.return_value
        mock_config_instance.load.return_value.audio_feedback = False
        mock_config_instance.load.return_value.max_recording_duration = 0
        mock_config_instance.load.return_value.clipboard_clear_delay = 1.0
        mock_config_instance.load.return_value.word_overrides = {}
        mock_config_instance.load.return_value.paste_mode = "ctrl"
        mock_config_instance.load.return_value.post_processing = ""
        mock_config_instance.load.return_value.clipboard_behavior = False
        mock_config_instance.model_dir.return_value = "dummy"

        # Mock Parakeet transcribe return
        mock_parakeet.return_value.transcribe.return_value = "test transcription"

        # Initialize App
        app = ChirpApp()

        # Mock executor to prevent automatic background execution
        app._executor = MagicMock()

        # Mock the status indicator
        app.status_indicator = MagicMock()

        # 1. Start Recording
        app._start_recording()

        # Verify status update to "Recording..."
        app.status_indicator.update.assert_called_with("[bold red]Recording...[/bold red]", spinner="point")

        # 2. Stop Recording
        # Prepare dummy waveform
        mock_capture.return_value.stop.return_value = np.zeros(16000)

        app._stop_recording()

        # Verify status update to "Transcribing..."
        app.status_indicator.update.assert_called_with("[bold green]Transcribing...[/bold green]", spinner="dots")

        # Verify that the task was submitted
        app._executor.submit.assert_called()

        # 3. Transcribe completion
        # Call _transcribe_and_inject directly to verify the reset logic.

        waveform = np.zeros(16000)
        app._transcribe_and_inject(waveform)

        # Verify status reset to "Ready"
        app.status_indicator.update.assert_called_with("Ready", spinner="dots")

if __name__ == "__main__":
    unittest.main()
