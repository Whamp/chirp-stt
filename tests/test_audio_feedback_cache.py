import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
import logging

from chirp.audio_feedback import AudioFeedback

class TestAudioFeedbackCache(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock(spec=logging.Logger)

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.winsound", None) # Force sounddevice path
    @patch("chirp.audio_feedback.wave")
    @patch("chirp.audio_feedback.np")
    def test_caching_sounddevice(self, mock_np, mock_wave, mock_sd):
        # Setup mocks
        mock_wf = MagicMock()
        mock_wave.open.return_value.__enter__.return_value = mock_wf
        mock_wf.getframerate.return_value = 44100
        mock_wf.getnchannels.return_value = 1
        mock_wf.readframes.return_value = b"data"

        mock_audio_data = MagicMock()
        mock_np.frombuffer.return_value = mock_audio_data

        # Initialize
        af = AudioFeedback(logger=self.logger, enabled=True)

        # First call
        af.play_start()

        # Second call
        af.play_start()

        # Assert wave.open called ONLY ONCE
        self.assertEqual(mock_wave.open.call_count, 1)

        # Assert play called twice
        self.assertEqual(mock_sd.play.call_count, 2)

    @patch("chirp.audio_feedback.sd", None)
    @patch("chirp.audio_feedback.winsound")  # Force winsound path
    def test_caching_winsound(self, mock_winsound):
        # Setup mocks
        mock_winsound.SND_FILENAME = 0x20000
        mock_winsound.SND_ASYNC = 0x0001

        # Initialize
        af = AudioFeedback(logger=self.logger, enabled=True)

        # First call
        af.play_start()

        # Second call
        af.play_start()

        # Assert PlaySound called twice
        self.assertEqual(mock_winsound.PlaySound.call_count, 2)

        # Verify both calls used file path string and SND_FILENAME (not SND_MEMORY)
        for call in mock_winsound.PlaySound.call_args_list:
            args, _ = call
            data, flags = args
            self.assertIsInstance(data, str)  # File path, not bytes
            self.assertTrue(flags & mock_winsound.SND_FILENAME)
            self.assertTrue(flags & mock_winsound.SND_ASYNC)

if __name__ == "__main__":
    unittest.main()
