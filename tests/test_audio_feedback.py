import sys
import unittest
from unittest.mock import MagicMock, patch
import importlib

class TestAudioFeedback(unittest.TestCase):
    def test_play_sound_uses_sounddevice(self):
        """Test that play_start calls sounddevice.play when winsound is missing."""
        mock_sd = MagicMock()
        mock_wave = MagicMock()
        mock_np = MagicMock()
        mock_logger = MagicMock()

        # Patch modules
        with patch.dict(sys.modules, {
            "sounddevice": mock_sd,
            "winsound": None,
            "numpy": mock_np,
            "wave": mock_wave
        }):
            # Force reload/import of the module under test to pick up patched modules
            if "chirp.audio_feedback" in sys.modules:
                del sys.modules["chirp.audio_feedback"]

            from chirp import audio_feedback
            importlib.reload(audio_feedback)

            # Setup the instance
            af = audio_feedback.AudioFeedback(logger=mock_logger, enabled=True)

            # Verify enabled logic
            self.assertTrue(af._enabled)

            # Prepare mocks for execution
            mock_wf = MagicMock()
            mock_wave.open.return_value.__enter__.return_value = mock_wf
            mock_wf.getframerate.return_value = 44100
            mock_wf.getnchannels.return_value = 1
            mock_wf.readframes.return_value = b'data'

            mock_data = MagicMock()
            mock_np.frombuffer.return_value = mock_data

            # Run method
            af.play_start(override_path="test.wav")

            # Assertions
            mock_wave.open.assert_called_with("test.wav", "rb")
            mock_sd.play.assert_called_with(mock_data, 44100)

    def test_audio_feedback_disabled_if_backends_missing(self):
        """Test that it disables itself if no backend is available."""
        mock_logger = MagicMock()

        # Simulate missing modules
        with patch.dict(sys.modules, {
            "sounddevice": None,
            "winsound": None,
        }):
             if "chirp.audio_feedback" in sys.modules:
                del sys.modules["chirp.audio_feedback"]

             from chirp import audio_feedback
             importlib.reload(audio_feedback)

             af = audio_feedback.AudioFeedback(logger=mock_logger, enabled=True)
             self.assertFalse(af._enabled)

if __name__ == "__main__":
    unittest.main()
