import sys
from unittest.mock import MagicMock, call

# Mock low-level dependencies before imports to avoid environment issues
sys.modules["sounddevice"] = MagicMock()
sys.modules["winsound"] = MagicMock()
sys.modules["keyboard"] = MagicMock()

import unittest
from unittest.mock import patch, ANY

# Import after mocking
from chirp.main import ChirpApp

class TestUIStatus(unittest.TestCase):
    @patch("chirp.main.get_logger")
    @patch("chirp.main.ConfigManager")
    @patch("chirp.main.ParakeetManager")
    @patch("chirp.main.AudioCapture")
    @patch("chirp.main.AudioFeedback")
    @patch("chirp.main.KeyboardShortcutManager")
    @patch("chirp.main.TextInjector")
    @patch("chirp.main.Console") # Mock the Console class used in main.py
    def test_status_lifecycle(self, MockConsole, MockInjector, MockKeyboard, MockFeedback, MockCapture, MockParakeet, MockConfig, MockGetLogger):
        """Verify that the UI status indicator transitions correctly through states."""

        # Setup mocks
        mock_console_instance = MockConsole.return_value
        mock_status = MagicMock()
        mock_console_instance.status.return_value = mock_status

        # Mock Config
        mock_config = MockConfig.return_value.load.return_value
        mock_config.max_recording_duration = 0
        mock_config.audio_feedback = False

        # Ensure logger has no RichHandler
        mock_logger = MockGetLogger.return_value
        mock_logger.handlers = []

        # Initialize App
        app = ChirpApp()

        # Prevent ThreadPoolExecutor from actually running the task in background during test to avoid race
        # We can just verify _executor.submit was called, and manually call _transcribe_and_inject
        app._executor = MagicMock()

        # 1. Verify initialization
        self.assertTrue(hasattr(app, "status_indicator"))
        mock_console_instance.status.assert_any_call("Ready", spinner="dots")

        # 2. Test Start Recording
        app._start_recording()
        mock_status.update.assert_called_with("Recording...", spinner="point")

        # 3. Test Stop Recording
        app.audio_capture.stop.return_value = MagicMock(size=100)
        app._stop_recording()
        # Should set to Transcribing
        mock_status.update.assert_called_with("Transcribing...", spinner="dots")

        # Verify task submitted
        app._executor.submit.assert_called_with(app._transcribe_and_inject, ANY)

        # 4. Test Transcribe Finished
        # Manually call the worker method
        app._transcribe_and_inject(MagicMock(size=100))
        mock_status.update.assert_called_with("Ready", spinner="dots")

    @patch("chirp.main.get_logger")
    @patch("chirp.main.ConfigManager")
    @patch("chirp.main.ParakeetManager")
    @patch("chirp.main.AudioCapture")
    @patch("chirp.main.AudioFeedback")
    @patch("chirp.main.KeyboardShortcutManager")
    @patch("chirp.main.TextInjector")
    @patch("chirp.main.Console")
    def test_run_wraps_keyboard_wait(self, MockConsole, MockInjector, MockKeyboard, MockFeedback, MockCapture, MockParakeet, MockConfig, MockGetLogger):
        """Verify that app.run() wraps keyboard.wait() in the status context."""
        mock_console_instance = MockConsole.return_value
        mock_status = MagicMock()
        mock_console_instance.status.return_value = mock_status

        # Mock Config
        mock_config = MockConfig.return_value.load.return_value
        mock_config.max_recording_duration = 0

        app = ChirpApp()

        app.run()

        mock_status.__enter__.assert_called()
        app.keyboard.wait.assert_called()
        mock_status.__exit__.assert_called()

if __name__ == "__main__":
    unittest.main()
