import sys
import unittest
from unittest import mock
from pathlib import Path

# Mock winsound before importing audio_feedback
mock_winsound = mock.Mock()
mock_winsound.SND_FILENAME = 131072
mock_winsound.SND_ASYNC = 1
mock_winsound.MB_ICONHAND = 16


class TestAudioFeedback(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to inject the mock winsound
        self.winsound_patcher = mock.patch.dict(
            sys.modules, {"winsound": mock_winsound}
        )
        self.winsound_patcher.start()

        # Add src to sys.path if not present
        src_path = str(Path(__file__).resolve().parents[1] / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        # Import AudioFeedback after patching
        from chirp.audio_feedback import AudioFeedback

        self.AudioFeedback = AudioFeedback

        self.logger = mock.Mock()
        self.feedback = self.AudioFeedback(logger=self.logger, enabled=True)

        # Reset mocks
        mock_winsound.PlaySound.reset_mock()
        mock_winsound.MessageBeep.reset_mock()

    def tearDown(self):
        self.winsound_patcher.stop()

    def test_play_start_default(self):
        self.feedback.play_start()
        mock_winsound.PlaySound.assert_called()
        args, _ = mock_winsound.PlaySound.call_args
        self.assertIn("ping-up.wav", str(args[0]))
        self.assertEqual(args[1], mock_winsound.SND_FILENAME | mock_winsound.SND_ASYNC)

    def test_play_stop_default(self):
        self.feedback.play_stop()
        mock_winsound.PlaySound.assert_called()
        args, _ = mock_winsound.PlaySound.call_args
        self.assertIn("ping-down.wav", str(args[0]))

    def test_play_start_override(self):
        self.feedback.play_start(override_path="custom_start.wav")
        mock_winsound.PlaySound.assert_called()
        args, _ = mock_winsound.PlaySound.call_args
        self.assertEqual(str(args[0]), "custom_start.wav")

    def test_play_error_default(self):
        self.feedback.play_error()
        mock_winsound.MessageBeep.assert_called_with(mock_winsound.MB_ICONHAND)

    def test_play_error_override(self):
        self.feedback.play_error(override_path="custom_error.wav")
        mock_winsound.PlaySound.assert_called()
        args, _ = mock_winsound.PlaySound.call_args
        self.assertEqual(str(args[0]), "custom_error.wav")


if __name__ == "__main__":
    unittest.main()
