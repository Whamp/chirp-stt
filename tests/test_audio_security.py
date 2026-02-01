import logging
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from chirp.audio_feedback import AudioFeedback, MAX_AUDIO_FILE_SIZE_BYTES


class TestAudioSecurity(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.np")
    @patch("chirp.audio_feedback.wave")
    @patch("pathlib.Path.stat")
    def test_load_and_cache_large_file_raises_error(self, mock_stat, mock_wave, mock_np, mock_sd):
        """Should raise ValueError if audio file exceeds size limit."""
        # Mock file size > 5MB
        mock_stat.return_value.st_size = MAX_AUDIO_FILE_SIZE_BYTES + 1

        af = AudioFeedback(logger=self.mock_logger, enabled=True)
        # Force use_sounddevice to true to trigger the loading logic
        af._use_sounddevice = True

        with self.assertRaises(ValueError) as cm:
            af._load_and_cache(Path("/fake/large_file.wav"), "key")

        self.assertIn("Audio file too large", str(cm.exception))

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.np")
    @patch("chirp.audio_feedback.wave")
    @patch("pathlib.Path.stat")
    def test_load_and_cache_valid_file_proceeds(self, mock_stat, mock_wave, mock_np, mock_sd):
        """Should proceed if audio file is within size limit."""
        # Mock file size <= 5MB
        mock_stat.return_value.st_size = MAX_AUDIO_FILE_SIZE_BYTES

        # Mock wave open stuff
        mock_wf = MagicMock()
        mock_wave.open.return_value.__enter__.return_value = mock_wf
        mock_wf.readframes.return_value = b""
        mock_wf.getnchannels.return_value = 1
        mock_wf.getframerate.return_value = 16000
        mock_wf.getnframes.return_value = 0

        mock_np.frombuffer.return_value = MagicMock()

        af = AudioFeedback(logger=self.mock_logger, enabled=True)
        af._use_sounddevice = True

        try:
            af._load_and_cache(Path("/fake/valid_file.wav"), "key")
        except ValueError:
            self.fail("_load_and_cache raised ValueError unexpectedly!")

if __name__ == "__main__":
    unittest.main()
