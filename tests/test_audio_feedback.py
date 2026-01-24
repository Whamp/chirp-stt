import logging
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from chirp.audio_feedback import AudioFeedback


class TestAudioFeedback(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock(spec=logging.Logger)

    @patch("chirp.audio_feedback.sd", new=MagicMock())
    @patch("chirp.audio_feedback.winsound", None)
    def test_enabled_when_sounddevice_available(self):
        """AudioFeedback should be enabled when sounddevice is available."""
        # On Linux, winsound is None but sounddevice should be available
        af = AudioFeedback(logger=self.mock_logger, enabled=True)
        # Since we're on Linux and sounddevice is installed, should be enabled
        self.assertTrue(af._enabled)

    def test_disabled_when_explicitly_disabled(self):
        """AudioFeedback should respect enabled=False."""
        af = AudioFeedback(logger=self.mock_logger, enabled=False)
        self.assertFalse(af._enabled)

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.winsound", None)
    def test_play_with_sounddevice_called(self, mock_sd):
        """When winsound is None, should use sounddevice path (via cache)."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True)

        # Mock the internal methods
        af._load_and_cache = MagicMock(return_value="data")
        af._play_cached = MagicMock()

        with patch.object(af, "_get_sound_path") as mock_get_path:
            mock_get_path.return_value.__enter__ = MagicMock(return_value=Path("/fake/path.wav"))
            mock_get_path.return_value.__exit__ = MagicMock(return_value=False)

            af.play_start()

            af._load_and_cache.assert_called_once()
            af._play_cached.assert_called_once_with("data")

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.np")
    @patch("chirp.audio_feedback.wave")
    def test_load_and_cache_sounddevice(self, mock_wave, mock_np, mock_sd):
        """_load_and_cache should read WAV and cache data."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True)

        # Setup wave mock
        mock_wf = MagicMock()
        mock_wave.open.return_value.__enter__.return_value = mock_wf
        mock_wf.getframerate.return_value = 44100
        mock_wf.getnchannels.return_value = 1
        mock_wf.getnframes.return_value = 1000
        mock_wf.readframes.return_value = b"\x00" * 2000

        mock_audio_data = MagicMock()
        mock_np.frombuffer.return_value = mock_audio_data

        key = "test_key"
        data = af._load_and_cache(Path("/fake/sound.wav"), key)

        mock_wave.open.assert_called_with("/fake/sound.wav", "rb")
        mock_np.frombuffer.assert_called()

        # Check returned data and cache
        expected = (mock_audio_data, 44100)
        self.assertEqual(data, expected)
        self.assertEqual(af._cache[key], expected)

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.winsound", None)
    def test_play_cached_sounddevice(self, mock_sd):
        """_play_cached should call sd.play."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True)
        mock_data = (MagicMock(), 44100)
        af._play_cached(mock_data)
        mock_sd.play.assert_called_with(mock_data[0], 44100)

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.np")
    @patch("chirp.audio_feedback.winsound", None)
    def test_play_cached_passes_data(self, mock_np, mock_sd):
        """_play_cached should pass data directly to sd.play without scaling."""
        import numpy as np

        # Create real numpy array for testing
        mock_np.int16 = np.int16
        mock_np.float32 = np.float32

        af = AudioFeedback(logger=self.mock_logger, enabled=True, volume=0.5)

        # Use real numpy array
        audio_data = np.array([1000, -1000, 2000], dtype=np.int16)
        mock_data = (audio_data, 44100)

        af._play_cached(mock_data)

        # Verify sd.play was called
        mock_sd.play.assert_called_once()
        call_args = mock_sd.play.call_args[0]
        played_audio = call_args[0]
        samplerate = call_args[1]

        # Check data was passed through WITHOUT scaling (scaling happens in load)
        self.assertEqual(samplerate, 44100)
        self.assertEqual(played_audio[0], 1000)
        self.assertEqual(played_audio[1], -1000)
        self.assertEqual(played_audio[2], 2000)

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.np")
    @patch("chirp.audio_feedback.wave")
    @patch("chirp.audio_feedback.winsound", None)
    def test_load_and_cache_scales_volume(self, mock_wave, mock_np, mock_sd):
        """_load_and_cache should scale audio when volume < 1.0."""
        import numpy as np

        # Create real numpy array for testing
        mock_np.int16 = np.int16
        mock_np.float32 = np.float32
        # mock_np.frombuffer is mocked by MagicMock by default, we override it below

        af = AudioFeedback(logger=self.mock_logger, enabled=True, volume=0.5)

        # Setup wave mock
        mock_wf = MagicMock()
        mock_wave.open.return_value.__enter__.return_value = mock_wf
        mock_wf.getframerate.return_value = 44100
        mock_wf.getnchannels.return_value = 1
        mock_wf.readframes.return_value = b"\x00" * 10  # dummy data

        # Use a real array for frombuffer so we can test scaling
        real_data = np.array([1000, -1000, 2000], dtype=np.int16)
        mock_np.frombuffer = MagicMock(return_value=real_data)

        key = "test_key_scaling"
        data = af._load_and_cache(Path("/fake/sound.wav"), key)

        # Check returned data is scaled
        audio_data, samplerate = data
        self.assertEqual(samplerate, 44100)
        self.assertEqual(audio_data[0], 500)
        self.assertEqual(audio_data[1], -500)
        self.assertEqual(audio_data[2], 1000)

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.winsound", None)
    def test_volume_clamp_above_one(self, mock_sd):
        """Volume should be clamped to 1.0 if above."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True, volume=1.5)
        self.assertEqual(af._volume, 1.0)

    @patch("chirp.audio_feedback.sd")
    @patch("chirp.audio_feedback.winsound", None)
    def test_volume_clamp_below_zero(self, mock_sd):
        """Volume should be clamped to 0.0 if below."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True, volume=-0.5)
        self.assertEqual(af._volume, 0.0)

    @patch("chirp.audio_feedback.sd", None)
    @patch("chirp.audio_feedback.np", None)
    @patch("chirp.audio_feedback.winsound", MagicMock())
    def test_volume_warning_when_sounddevice_unavailable(self):
        """Should warn when volume < 1.0 but sounddevice is unavailable."""
        af = AudioFeedback(logger=self.mock_logger, enabled=True, volume=0.5)
        self.mock_logger.warning.assert_called()
        # Should still work, just at full volume
        self.assertTrue(af._enabled)


if __name__ == "__main__":
    unittest.main()
