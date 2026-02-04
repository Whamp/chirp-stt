import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging

from chirp.audio_feedback import AudioFeedback

class TestAudioSecurity(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test_logger")

    @patch("chirp.audio_feedback.sd", new=MagicMock())
    @patch("chirp.audio_feedback.winsound", None)
    @patch("chirp.audio_feedback.wave")
    @patch("chirp.audio_feedback.np")
    def test_audio_file_size_limit(self, mock_np, mock_wave):
        """Verify that files larger than 5MB are rejected."""
        # Ensure AudioFeedback thinks sounddevice is available so it tries to load/read the file
        mock_np.frombuffer = MagicMock()

        af = AudioFeedback(logger=self.logger, enabled=True)

        # Mock file path and stat
        mock_path = MagicMock(spec=Path)
        mock_path.stat.return_value.st_size = 6 * 1024 * 1024  # 6MB
        mock_path.__str__.return_value = "/fake/large_file.wav"

        # We expect this to fail AFTER we implement the fix.
        # For now, without the fix, it would proceed to open the file via wave.open.
        # So if we run this NOW, it should fail the assertion (it won't raise ValueError).
        # Or it might fail because wave.open mock isn't fully set up for reading.
        # But my goal is to verify the fix later.

        # Setup mock_wave so it doesn't crash if called
        mock_wf = MagicMock()
        mock_wave.open.return_value.__enter__.return_value = mock_wf
        mock_wf.getframerate.return_value = 44100
        mock_wf.getnchannels.return_value = 1
        mock_wf.readframes.return_value = b""
        mock_wf.getnframes.return_value = 0

        with self.assertRaises(ValueError) as cm:
            af._load_and_cache(mock_path, "test_key")

        self.assertIn("Audio file too large", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
