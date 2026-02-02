import logging
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from chirp.audio_feedback import AudioFeedback


class TestAudioSecurity(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)

    @patch("chirp.audio_feedback.sd", new=MagicMock())
    @patch("chirp.audio_feedback.wave")
    @patch("chirp.audio_feedback.np")
    @patch("chirp.audio_feedback.winsound", None)
    def test_rejects_large_files(self, mock_np, mock_wave):
        """AudioFeedback should reject files larger than 5MB."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True)

        # Mock Path.stat() to return a large size
        with patch.object(Path, "stat") as mock_stat:
            # 5MB + 1 byte
            mock_stat.return_value.st_size = 5 * 1024 * 1024 + 1

            # Mock wave.open to behave normally (if check fails, this would be called)
            mock_wf = MagicMock()
            mock_wave.open.return_value.__enter__.return_value = mock_wf
            mock_wf.getframerate.return_value = 44100
            mock_wf.getnchannels.return_value = 1
            mock_wf.readframes.return_value = b"\x00"
            mock_wf.getnframes.return_value = 1
            mock_np.frombuffer.return_value = MagicMock()

            # We expect ValueError. If the check is missing, this block will finish
            # without raising ValueError (because we mocked wave.open), causing the test to fail.
            with self.assertRaises(ValueError) as cm:
                af._load_and_cache(Path("large_file.wav"), "key")

            self.assertIn("exceeds size limit", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
