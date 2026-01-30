import unittest
from unittest.mock import MagicMock, patch
import logging
from pathlib import Path

from chirp.audio_feedback import AudioFeedback, MAX_AUDIO_FILE_SIZE_BYTES

class TestAudioSecurity(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("TestLogger")
        self.logger.setLevel(logging.CRITICAL)

        # Instantiate AudioFeedback
        self.audio_feedback = AudioFeedback(
            logger=self.logger,
            enabled=True,
            volume=0.5
        )

    @patch("pathlib.Path.stat")
    def test_large_file_rejection(self, mock_stat):
        """Test that files larger than the limit are rejected."""
        # Limit + 1 byte
        large_size = MAX_AUDIO_FILE_SIZE_BYTES + 1
        mock_stat.return_value.st_size = large_size

        test_path = Path("fake_large_file.wav")

        # Expect ValueError because of size limit
        with self.assertRaises(ValueError) as cm:
            self.audio_feedback._load_and_cache(test_path, "test_key")

        self.assertIn("File size exceeds limit", str(cm.exception))

if __name__ == "__main__":
    unittest.main()
