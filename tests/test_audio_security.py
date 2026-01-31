import logging
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from chirp.audio_feedback import AudioFeedback

class TestAudioSecurity(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)

    @patch("chirp.audio_feedback.sd", new=MagicMock())
    @patch("chirp.audio_feedback.winsound", None)
    def test_load_and_cache_rejects_large_files(self):
        """_load_and_cache should raise ValueError if file exceeds size limit."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True)

        # Mock Path.stat to return a large size
        large_size = 6 * 1024 * 1024  # 6MB

        # We patch Path.stat so that any Path object's stat() method returns our mock
        with patch.object(Path, "stat") as mock_stat:
            mock_stat.return_value.st_size = large_size

            # We don't need to mock wave.open because it should fail BEFORE opening the file
            # If it tries to open, it means the security check failed (or doesn't exist)
            # and potentially would raise FileNotFoundError since the file doesn't exist,
            # but we want to assert it raises ValueError specifically due to size.

            # To distinguish from FileNotFoundError (if it proceeds to open),
            # we rely on the specific ValueError expectation.

            with self.assertRaises(ValueError) as cm:
                af._load_and_cache(Path("fake_large_file.wav"), "key")

            self.assertIn("too large", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
