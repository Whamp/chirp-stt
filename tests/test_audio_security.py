import logging
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from chirp.audio_feedback import AudioFeedback

class TestAudioSecurity(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.winsound", None)
    @patch("chirp.audio_feedback.wave")
    @patch("chirp.audio_feedback.np")
    def test_load_large_file_raises_error(self, mock_np, mock_wave, mock_sd):
        """Should raise ValueError if audio file is too large."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True)

        # Setup basic wave mock to avoid TypeError if check is missing
        mock_wf = MagicMock()
        mock_wave.open.return_value.__enter__.return_value = mock_wf
        mock_wf.getnchannels.return_value = 1
        mock_wf.getframerate.return_value = 44100
        mock_wf.readframes.return_value = b""
        mock_np.frombuffer.return_value = MagicMock()

        # Mock file size > 5MB
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 6 * 1024 * 1024  # 6MB

            with self.assertRaises(ValueError) as cm:
                af._load_and_cache(Path("/fake/huge.wav"), "test_key")

            self.assertIn("exceeds size limit", str(cm.exception))

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.winsound", None)
    @patch("chirp.audio_feedback.wave")
    @patch("chirp.audio_feedback.np")
    def test_load_valid_file_size(self, mock_np, mock_wave, mock_sd):
        """Should succeed if audio file is within size limit."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True)

        # Mock valid file size
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = 1024  # 1KB

            # Setup wave mock to return dummy data
            mock_wf = MagicMock()
            mock_wave.open.return_value.__enter__.return_value = mock_wf
            mock_wf.getnchannels.return_value = 1
            mock_wf.getframerate.return_value = 44100
            mock_wf.readframes.return_value = b"\x00"
            mock_np.frombuffer.return_value = MagicMock()

            # Should not raise
            af._load_and_cache(Path("/fake/small.wav"), "test_key")

if __name__ == "__main__":
    unittest.main()
