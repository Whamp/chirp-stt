import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from chirp.audio_feedback import AudioFeedback

class TestAudioSecurity(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock()

    @patch("chirp.audio_feedback.sd", new=MagicMock())  # Ensure enabled=True works
    def test_audio_file_too_large(self):
        """AudioFeedback should raise ValueError for files > 5MB."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True)

        # Mock path and stat
        mock_path = MagicMock(spec=Path)
        # 5MB + 1 byte
        mock_path.stat.return_value.st_size = 5 * 1024 * 1024 + 1

        with self.assertRaises(ValueError) as cm:
            af._load_and_cache(mock_path, "key")

        self.assertIn("Audio file too large", str(cm.exception))

    @patch("chirp.audio_feedback.sd", new=MagicMock())
    @patch("chirp.audio_feedback.wave")
    @patch("chirp.audio_feedback.np")
    def test_audio_file_size_ok(self, mock_np, mock_wave):
        """AudioFeedback should accept files <= 5MB."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True)

        # Mock path and stat
        mock_path = MagicMock(spec=Path)
        mock_path.stat.return_value.st_size = 5 * 1024 * 1024 # Exactly 5MB
        mock_path.__str__.return_value = "/fake/file.wav"

        # Mock wave reading internals to avoid errors
        mock_wf = MagicMock()
        mock_wave.open.return_value.__enter__.return_value = mock_wf
        mock_wf.getnchannels.return_value = 1
        mock_wf.readframes.return_value = b""
        mock_np.frombuffer.return_value = MagicMock() # Mock array

        try:
            af._load_and_cache(mock_path, "key")
        except ValueError:
            self.fail("AudioFeedback raised ValueError for valid file size")

if __name__ == "__main__":
    unittest.main()
