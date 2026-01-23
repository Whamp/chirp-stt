import unittest
from unittest.mock import MagicMock, patch, mock_open
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

    @patch("builtins.open", new_callable=mock_open, read_data=b"soundbytes")
    @patch("chirp.audio_feedback.sd", None)
    @patch("chirp.audio_feedback.winsound") # Force winsound path
    def test_caching_winsound(self, mock_winsound, mock_file):
        # Setup mocks
        mock_winsound.SND_FILENAME = 0x20000
        mock_winsound.SND_ASYNC = 0x0001
        mock_winsound.SND_MEMORY = 0x0004

        # Initialize
        af = AudioFeedback(logger=self.logger, enabled=True)

        # First call
        af.play_start()

        # Second call
        af.play_start()

        # Assert PlaySound called twice
        self.assertEqual(mock_winsound.PlaySound.call_count, 2)

        # Verify both calls used bytes and SND_MEMORY
        for call in mock_winsound.PlaySound.call_args_list:
            args, _ = call
            data, flags = args
            self.assertEqual(data, b"soundbytes")
            self.assertTrue(flags & mock_winsound.SND_MEMORY)
            self.assertTrue(flags & mock_winsound.SND_ASYNC)

        # Verify open called ONLY ONCE
        # Note: Depending on implementation, resources.as_file might open files too?
        # But our code calls open(path, "rb") explicitly in _load_and_cache.
        # resources.as_file yields a path.
        # We assume resources.as_file doesn't call open on the file itself in a way mock catches it?
        # Actually builtins.open is used by resources too if it extracts?
        # If it's a file on disk (development mode), resources.as_file returns path.
        # So explicit open calls should be 1.
        self.assertEqual(mock_file.call_count, 1)

if __name__ == "__main__":
    unittest.main()
