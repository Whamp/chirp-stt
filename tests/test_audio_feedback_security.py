import logging
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from chirp.audio_feedback import AudioFeedback


class TestAudioFeedbackSecurity(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.np")
    @patch("chirp.audio_feedback.wave")
    @patch("chirp.audio_feedback.winsound", None)
    def test_load_large_file_raises_error(self, mock_wave, mock_np, mock_sd):
        """_load_and_cache should raise an error if the audio file is too large."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True)

        # Mock wave reading to simulate a large file (e.g. > 10MB)
        mock_wf = MagicMock()
        mock_wave.open.return_value.__enter__.return_value = mock_wf
        mock_wf.getframerate.return_value = 44100
        mock_wf.getnchannels.return_value = 2
        mock_wf.getsampwidth.return_value = 2
        # 2 channels * 2 bytes = 4 bytes per frame.
        # 3,000,000 frames * 4 bytes = 12 MB.
        mock_wf.getnframes.return_value = 3_000_000

        # We expect this to raise a ValueError or similar
        with self.assertRaises(ValueError) as cm:
            af._load_and_cache(Path("/fake/large_sound.wav"), "large_sound")

        self.assertIn("too large", str(cm.exception))

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.np")
    @patch("chirp.audio_feedback.wave")
    @patch("chirp.audio_feedback.winsound", None)
    def test_load_small_file_succeeds(self, mock_wave, mock_np, mock_sd):
        """_load_and_cache should succeed for small files."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True)

        # Mock wave reading to simulate a small file
        mock_wf = MagicMock()
        mock_wave.open.return_value.__enter__.return_value = mock_wf
        mock_wf.getframerate.return_value = 44100
        mock_wf.getnchannels.return_value = 1
        mock_wf.getsampwidth.return_value = 2
        # 1000 frames * 2 bytes = 2000 bytes.
        mock_wf.getnframes.return_value = 1000
        mock_wf.readframes.return_value = b"\x00" * 2000

        mock_np.frombuffer.return_value = MagicMock()

        af._load_and_cache(Path("/fake/small_sound.wav"), "small_sound")
        # Should not raise
