import unittest
from unittest.mock import MagicMock, patch
import sys
import types

# Mock sounddevice globally because it's missing in the test environment
# and imported at top-level by chirp.audio_capture
if "sounddevice" not in sys.modules:
    mock_sd = types.ModuleType("sounddevice")
    mock_sd.InputStream = MagicMock()
    sys.modules["sounddevice"] = mock_sd

# Mock winsound if on Windows
if sys.platform == "win32" and "winsound" not in sys.modules:
    mock_winsound = types.ModuleType("winsound")
    sys.modules["winsound"] = mock_winsound

# Mock keyboard (imported by main.py -> keyboard_shortcuts.py)
if "keyboard" not in sys.modules:
    mock_keyboard_lib = types.ModuleType("keyboard")
    sys.modules["keyboard"] = mock_keyboard_lib

# Mock pyperclip (imported by text_injector.py)
if "pyperclip" not in sys.modules:
    mock_pyperclip = types.ModuleType("pyperclip")
    mock_pyperclip.copy = MagicMock()
    mock_pyperclip.paste = MagicMock()
    mock_pyperclip.PyperclipException = Exception
    sys.modules["pyperclip"] = mock_pyperclip

from chirp.main import ChirpApp

class TestUIStatus(unittest.TestCase):
    @patch("chirp.main.ParakeetManager")
    @patch("chirp.main.AudioCapture")
    @patch("chirp.main.AudioFeedback")
    @patch("chirp.main.KeyboardShortcutManager")
    @patch("chirp.main.ConfigManager")
    @patch("chirp.main.Console")
    @patch("chirp.main.get_logger")
    def test_status_lifecycle(self, mock_get_logger, MockConsole, MockConfigManager, MockKeyboard, MockAudioFeedback, MockAudioCapture, MockParakeet):
        # Setup mocks
        mock_console_instance = MockConsole.return_value
        mock_status = MagicMock()
        mock_console_instance.status.return_value = mock_status

        # Mock logger to ensure no handlers so ChirpApp uses patched Console
        mock_logger = MagicMock()
        mock_logger.handlers = []
        mock_get_logger.return_value = mock_logger

        # Mock config
        mock_config = MockConfigManager.return_value.load.return_value
        mock_config.parakeet_model = "test-model"
        mock_config.audio_feedback = True
        mock_config.error_sound_path = None
        mock_config.start_sound_path = None
        mock_config.stop_sound_path = None
        mock_config.max_recording_duration = 0
        mock_config.clipboard_clear_delay = 0.5
        mock_config.paste_mode = "ctrl"
        mock_config.word_overrides = {}
        mock_config.post_processing = ""
        mock_config.clipboard_behavior = False
        mock_config.threads = 1
        mock_config.onnx_providers = "cpu"
        mock_config.parakeet_quantization = None
        mock_config.model_timeout = 300.0
        mock_config.language = "en"
        mock_config.primary_shortcut = "ctrl+space"

        # Initialize app
        app = ChirpApp()

        # Verify status created (but not necessarily started for idle, or maybe "Idle" status created)
        # In my plan: self.status_indicator = self.console.status("Idle")
        mock_console_instance.status.assert_any_call("Idle")

        # Reset mock to clear initialization calls
        mock_status.reset_mock()

        # 1. Start Recording
        app._start_recording()

        # Verify status updated to recording
        mock_status.update.assert_called_with("[bold red]Recording...[/bold red]", spinner="point")
        mock_status.start.assert_called()

        # 2. Stop Recording
        # Mock waveform
        mock_waveform = MagicMock()
        mock_waveform.size = 16000
        app.audio_capture.stop.return_value = mock_waveform

        app._stop_recording()

        # Verify status updated to transcribing
        mock_status.update.assert_called_with("[bold green]Transcribing...[/bold green]", spinner="dots")

        # 3. Transcribe
        # This is usually called by executor, but we call directly for test
        app._transcribe_and_inject(mock_waveform)

        # Verify status stopped
        mock_status.stop.assert_called()

        # 4. Race condition check: If recording started again during transcribe
        mock_status.reset_mock()
        app._recording = True
        app._transcribe_and_inject(mock_waveform)

        # Verify status was NOT stopped
        mock_status.stop.assert_not_called()

if __name__ == "__main__":
    unittest.main()
