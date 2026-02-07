import sys
import unittest
from unittest.mock import MagicMock, patch

class TestChirpAppUI(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to mock hard dependencies
        self.modules_patcher = patch.dict(sys.modules, {
            "sounddevice": MagicMock(),
            "keyboard": MagicMock(),
            "pyperclip": MagicMock(),
            # We don't mock parakeet_manager module here, we rely on @patch in tests or it's safe to import
        })
        self.modules_patcher.start()

        # We need to import ChirpApp here, after mocking sys.modules
        # We use strict import to ensure we get the version using our mocks
        # If it was already imported by another test, we might need to reload it?
        # But for safety, we assume it wasn't, or we force reload if needed.
        # However, verifying 'reload' with mocks is tricky.

        # For now, just import. If it fails due to previous import, it means we have shared state.
        import chirp.main
        import importlib
        importlib.reload(chirp.main) # Force usage of mocked sounddevice/keyboard

        self.ChirpApp = chirp.main.ChirpApp

        # Setup mocks for class instance
        self.mock_logger = MagicMock()

        # We can't use @patch decorators easily on setUp if we want to patch imports inside chirp.main
        # because chirp.main is imported dynamically.
        # But we can patch 'chirp.main.ParakeetManager' using patch() context managers or start/stop.

        self.patches = []

        # Patch dependencies of ChirpApp
        p_pm = patch("chirp.main.ParakeetManager")
        self.mock_parakeet_cls = p_pm.start()
        self.patches.append(p_pm)

        p_ac = patch("chirp.main.AudioCapture")
        self.mock_capture_cls = p_ac.start()
        self.patches.append(p_ac)

        p_af = patch("chirp.main.AudioFeedback")
        self.mock_feedback_cls = p_af.start()
        self.patches.append(p_af)

        p_ti = patch("chirp.main.TextInjector")
        self.mock_injector_cls = p_ti.start()
        self.patches.append(p_ti)

        p_gl = patch("chirp.main.get_logger")
        self.mock_get_logger = p_gl.start()
        self.mock_get_logger.return_value = self.mock_logger
        self.patches.append(p_gl)

        p_exec = patch("chirp.main.concurrent.futures.ThreadPoolExecutor")
        self.mock_executor_cls = p_exec.start()
        self.patches.append(p_exec)

        p_timer = patch("chirp.main.threading.Timer")
        self.mock_timer = p_timer.start()
        self.patches.append(p_timer)

        # Prevent RichHandler from being used so we control console
        self.mock_logger.handlers = []

        # Initialize app
        self.app = self.ChirpApp()

        # Inject mock console and status
        self.mock_console = MagicMock()
        self.mock_status = MagicMock()
        self.app.console = self.mock_console

        # Manually set status indicator for testing methods in isolation
        self.app.status_indicator = self.mock_status

        # Ensure executor is a mock
        self.app._executor = self.mock_executor_cls.return_value

    def tearDown(self):
        for p in reversed(self.patches):
            p.stop()
        self.modules_patcher.stop()

        # Clean up sys.modules to prevent pollution
        to_remove = [k for k in sys.modules if k.startswith("chirp.main") or k.startswith("chirp.audio_capture")]
        for k in to_remove:
            del sys.modules[k]

    def test_start_recording_updates_status(self):
        """Test that starting recording updates the status spinner."""
        self.app._start_recording()

        # Verify status update
        self.mock_status.update.assert_called_with("[bold red]Recording...[/bold red]", spinner="point")

        # Verify logger called
        self.mock_logger.info.assert_any_call("Recording started")

    def test_stop_recording_updates_status(self):
        """Test that stopping recording updates the status spinner."""
        # Setup: pretend we are recording
        self.app._recording = True

        # Mock waveform
        mock_waveform = MagicMock()
        mock_waveform.size = 100
        self.app.audio_capture.stop.return_value = mock_waveform

        self.app._stop_recording()

        # Verify status update "Transcribing..." was called at some point
        self.mock_status.update.assert_any_call("[bold green]Transcribing...[/bold green]", spinner="dots")

    def test_transcribe_and_inject_updates_status(self):
        """Test that transcription updates status back to ready."""
        # Setup
        mock_waveform = MagicMock()
        mock_waveform.size = 100

        # Mock successful transcription
        self.app.parakeet.transcribe.return_value = "Test text"

        self.app._transcribe_and_inject(mock_waveform)

        # Verify status update back to ready
        self.mock_status.update.assert_any_call("Ready", spinner="dots")

    def test_transcribe_does_not_reset_status_if_recording(self):
        """Test that transcription does NOT reset status if recording started again."""
        # Setup
        mock_waveform = MagicMock()
        mock_waveform.size = 100

        # Mock successful transcription
        self.app.parakeet.transcribe.return_value = "Test text"

        # Simulate recording started during transcription
        self.app._recording = True

        self.app._transcribe_and_inject(mock_waveform)

        # Verify status calls
        calls = self.mock_status.update.call_args_list
        # Check that no call was made with "Ready"
        for call in calls:
            args, _ = call
            self.assertNotEqual(args[0], "Ready", "Should not set status to Ready if recording")

if __name__ == "__main__":
    unittest.main()
