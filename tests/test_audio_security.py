import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging

from chirp.audio_feedback import AudioFeedback

class TestAudioSecurity(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock(spec=logging.Logger)

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.winsound", None)
    @patch("chirp.audio_feedback.wave")
    @patch("chirp.audio_feedback.np")
    @patch("pathlib.Path.stat")
    def test_large_file_rejection(self, mock_stat, mock_np, mock_wave, mock_sd):
        # Setup mocks
        mock_wf = MagicMock()
        mock_wave.open.return_value.__enter__.return_value = mock_wf
        mock_wf.getframerate.return_value = 44100
        mock_wf.getnchannels.return_value = 1
        mock_wf.readframes.return_value = b"data"

        mock_audio_data = MagicMock()
        mock_np.frombuffer.return_value = mock_audio_data

        # Simulate a file size slightly larger than the limit (5MB + 1 byte)
        mock_stat.return_value.st_size = 5 * 1024 * 1024 + 1

        # Initialize
        af = AudioFeedback(logger=self.logger, enabled=True)

        # Try to load a custom sound
        af.play_start(override_path="large_file.wav")

        # Assert wave.open was NOT called (This will FAIL before fix)
        mock_wave.open.assert_not_called()

        # Assert logger warning (This will FAIL before fix)
        found = False
        for call in self.logger.warning.call_args_list:
            if "exceeds size limit" in str(call):
                found = True
                break
        self.assertTrue(found, "Warning about size limit not found")

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.winsound", None)
    @patch("chirp.audio_feedback.wave")
    @patch("chirp.audio_feedback.np")
    @patch("pathlib.Path.stat")
    def test_normal_file_acceptance(self, mock_stat, mock_np, mock_wave, mock_sd):
        # Setup mocks
        mock_wf = MagicMock()
        mock_wave.open.return_value.__enter__.return_value = mock_wf
        mock_wf.getframerate.return_value = 44100
        mock_wf.getnchannels.return_value = 1
        mock_wf.readframes.return_value = b"data"

        mock_audio_data = MagicMock()
        mock_np.frombuffer.return_value = mock_audio_data

        # Simulate a valid file size (5MB exactly)
        mock_stat.return_value.st_size = 5 * 1024 * 1024

        # Initialize
        af = AudioFeedback(logger=self.logger, enabled=True)

        # Try to load a custom sound
        af.play_start(override_path="normal_file.wav")

        # Assert wave.open WAS called
        mock_wave.open.assert_called_once()

if __name__ == "__main__":
    unittest.main()
