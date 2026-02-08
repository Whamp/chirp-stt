import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
import numpy as np

# Mock dependencies before importing ChirpApp
sys.modules["sounddevice"] = MagicMock()
sys.modules["keyboard"] = MagicMock()

# Since we modify sys.modules, we need to ensure chirp.main is reloaded or imported after mocks
# But here we are writing a script that will be executed fresh.
from chirp.main import ChirpApp

class TestUIStatus(unittest.TestCase):
    def setUp(self):
        # Patch dependencies
        self.patchers = []

        self.mock_logger = MagicMock()
        # Mock handlers to be empty list so loop works
        self.mock_logger.handlers = []
        patch_logger = patch("chirp.main.get_logger", return_value=self.mock_logger)
        self.patchers.append(patch_logger)
        patch_logger.start()

        # Mock ParakeetManager to avoid model loading
        self.mock_parakeet_cls = patch("chirp.main.ParakeetManager")
        self.mock_parakeet = self.mock_parakeet_cls.start()
        self.patchers.append(self.mock_parakeet_cls)

        # Mock AudioCapture
        self.mock_audio_capture_cls = patch("chirp.main.AudioCapture")
        self.mock_audio_capture = self.mock_audio_capture_cls.start()
        self.patchers.append(self.mock_audio_capture_cls)

        # Mock AudioFeedback
        self.mock_audio_feedback_cls = patch("chirp.main.AudioFeedback")
        self.mock_audio_feedback = self.mock_audio_feedback_cls.start()
        self.patchers.append(self.mock_audio_feedback_cls)

        # Mock TextInjector
        self.mock_text_injector_cls = patch("chirp.main.TextInjector")
        self.mock_text_injector = self.mock_text_injector_cls.start()
        self.patchers.append(self.mock_text_injector_cls)

        # Mock KeyboardShortcutManager
        self.mock_keyboard_cls = patch("chirp.main.KeyboardShortcutManager")
        self.mock_keyboard = self.mock_keyboard_cls.start()
        self.patchers.append(self.mock_keyboard_cls)

        # Mock Console and Status
        self.mock_console_cls = patch("chirp.main.Console")
        self.mock_console = self.mock_console_cls.start()
        self.patchers.append(self.mock_console_cls)

        # Setup mock status
        self.mock_status = MagicMock()
        # console.status(...) returns this mock status
        self.mock_console.return_value.status.return_value = self.mock_status

    def tearDown(self):
        for patcher in self.patchers:
            patcher.stop()

    def test_initialization_sets_ready_status(self):
        app = ChirpApp()
        # Verify status created with "Ready"
        app.console.status.assert_any_call("Ready", spinner="dots")
        self.assertEqual(app.status_indicator, self.mock_status)

    def test_run_activates_status(self):
        app = ChirpApp()
        app.run()
        # Verify status context manager used
        self.mock_status.__enter__.assert_called()
        # Verify keyboard wait called
        app.keyboard.wait.assert_called()
        self.mock_status.__exit__.assert_called()

    def test_start_recording_updates_status(self):
        app = ChirpApp()
        app.config.max_recording_duration = 0  # Disable timer
        app._start_recording()

        # Check update call
        self.mock_status.update.assert_called_with("Recording...", spinner="point", spinner_style="red")

    def test_stop_recording_updates_status(self):
        app = ChirpApp()
        # Simulate recording state
        app._recording = True

        # Mock executor submit to not run thread
        app._executor = MagicMock()

        app._stop_recording()

        # Check update call
        self.mock_status.update.assert_called_with("Transcribing...", spinner="dots", spinner_style="green")

    def test_transcription_resets_status_when_not_recording(self):
        app = ChirpApp()
        # Ensure not recording
        app._recording = False

        waveform = np.zeros(10)
        app._transcribe_and_inject(waveform)

        # Check reset to Ready
        self.mock_status.update.assert_called_with("Ready", spinner="dots", spinner_style="white")

    def test_transcription_does_not_reset_status_when_recording(self):
        app = ChirpApp()
        # Simulate recording started again during transcription
        app._recording = True

        waveform = np.zeros(10)
        app._transcribe_and_inject(waveform)

        # Check that update("Ready", ...) was NOT called
        ready_calls = [
            call for call in self.mock_status.update.mock_calls
            if len(call.args) > 0 and call.args[0] == "Ready"
        ]
        self.assertEqual(len(ready_calls), 0)

if __name__ == "__main__":
    unittest.main()
