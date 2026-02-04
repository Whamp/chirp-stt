import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock sounddevice before importing anything that uses it to prevent OSError
mock_sd = MagicMock()
sys.modules["sounddevice"] = mock_sd

from chirp.main import ChirpApp

class TestUIStatus(unittest.TestCase):
    def setUp(self):
        # Patch get_logger to prevent RichHandler interference and ensure we can mock Console
        self.logger_patcher = patch("chirp.main.get_logger")
        self.mock_get_logger = self.logger_patcher.start()
        # Ensure the logger has no handlers so ChirpApp creates a new Console
        self.mock_logger = MagicMock()
        self.mock_logger.handlers = []
        self.mock_get_logger.return_value = self.mock_logger

    def tearDown(self):
        self.logger_patcher.stop()

    @patch("chirp.main.ParakeetManager")
    @patch("chirp.main.AudioCapture")
    @patch("chirp.main.AudioFeedback")
    @patch("chirp.main.KeyboardShortcutManager")
    @patch("chirp.main.TextInjector")
    @patch("chirp.main.Console")
    def test_recording_and_transcribing_status(self, MockConsole, MockTextInjector, MockKeyboard, MockAudioFeedback, MockAudioCapture, MockParakeet):
        """Test that status indicators are updated correctly during recording and transcription."""

        # Setup mocks
        mock_console_instance = MockConsole.return_value
        mock_status = MagicMock()
        mock_console_instance.status.return_value = mock_status

        # Instantiate App
        app = ChirpApp(verbose=False)

        # Verify status initialized
        # assert_any_call because console.status is called again for Parakeet initialization
        mock_console_instance.status.assert_any_call("Ready")
        # self.assertEqual(app.status_indicator, mock_status) # This might fail if status() returns a new mock each time

        # 1. Start Recording
        app._start_recording()

        # Verify status updated to Recording
        mock_status.update.assert_called_with("[bold red]Recording...[/bold red]", spinner="point")
        mock_status.start.assert_called_once()

        # 2. Stop Recording
        # Verify status updated to Transcribing
        # Note: _stop_recording calls submit on executor. We need to mock executor to run immediately or checking logic.
        # But _stop_recording updates status BEFORE submitting.

        # Mock executor to prevent actual thread submission or just let it pass (it's a mock)
        app._executor = MagicMock()

        app._stop_recording()

        mock_status.update.assert_called_with("[bold green]Transcribing...[/bold green]", spinner="dots")

        # 3. Transcription Finished
        # Simulate the worker method running
        # We need to simulate waveform
        waveform = MagicMock()
        waveform.size = 1000

        # Case A: Not recording anymore -> should stop status
        app._recording = False
        app._transcribe_and_inject(waveform)
        mock_status.stop.assert_called_once()

        # Reset mock calls
        mock_status.stop.reset_mock()

        # Case B: Recording started again while transcribing -> should NOT stop status
        app._recording = True
        app._transcribe_and_inject(waveform)
        mock_status.stop.assert_not_called()

if __name__ == "__main__":
    unittest.main()
