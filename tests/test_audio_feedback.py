import unittest
from unittest.mock import MagicMock, patch
import sys
import logging
import numpy as np
import wave
import io
import struct

# Mock sounddevice before importing chirp.audio_feedback
sys.modules["sounddevice"] = MagicMock()
import sounddevice as sd

from chirp.audio_feedback import AudioFeedback

class TestAudioFeedback(unittest.TestCase):
    def setUp(self):
        self.logger = logging.getLogger("test")
        self.logger.addHandler(logging.NullHandler())
        # Reset mock
        sd.play.reset_mock()

    def create_dummy_wav(self, channels=1, sample_width=2, frame_rate=44100, frames=100):
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(frame_rate)
            # Generate silence/dummy data
            if sample_width == 1:
                data = bytes([128] * frames * channels)
            elif sample_width == 2:
                data = b'\x00\x00' * frames * channels
            elif sample_width == 4:
                data = b'\x00\x00\x00\x00' * frames * channels
            wf.writeframes(data)
        buffer.seek(0)
        return buffer

    def test_init_disabled(self):
        af = AudioFeedback(logger=self.logger, enabled=False)
        self.assertFalse(af._enabled)
        af.play_start()
        sd.play.assert_not_called()

    def test_init_enabled(self):
        af = AudioFeedback(logger=self.logger, enabled=True)
        self.assertTrue(af._enabled)

    @patch('chirp.audio_feedback.wave.open')
    @patch('chirp.audio_feedback.resources')
    def test_play_start_success(self, mock_resources, mock_wave_open):
        # Setup mock resource path
        mock_path = MagicMock()
        mock_path.__str__.return_value = "dummy.wav"

        # Setup context manager for resources.as_file
        cm = MagicMock()
        cm.__enter__.return_value = mock_path
        mock_resources.as_file.return_value = cm

        # Setup mock wave file
        # We need a real-ish wave object or mock it effectively
        mock_wf = MagicMock()
        mock_wf.getnchannels.return_value = 1
        mock_wf.getframerate.return_value = 16000
        mock_wf.getsampwidth.return_value = 2
        mock_wf.getnframes.return_value = 100
        mock_wf.readframes.return_value = b'\x00\x00' * 100

        mock_wave_open.return_value.__enter__.return_value = mock_wf

        af = AudioFeedback(logger=self.logger, enabled=True)
        af.play_start()

        sd.play.assert_called_once()
        args, _ = sd.play.call_args
        data, fs = args
        self.assertEqual(fs, 16000)
        self.assertEqual(data.shape, (100,))
        self.assertEqual(data.dtype, np.int16)

    @patch('chirp.audio_feedback.wave.open')
    def test_read_wav_16bit_mono(self, mock_wave_open):
        # Create a real wav in memory to test _read_wav logic properly if we could,
        # but _read_wav takes a path string.
        # So we trust the mock_wave_open to behave like wave.open

        mock_wf = MagicMock()
        mock_wf.getnchannels.return_value = 1
        mock_wf.getframerate.return_value = 44100
        mock_wf.getsampwidth.return_value = 2
        mock_wf.getnframes.return_value = 10
        # 10 frames * 2 bytes = 20 bytes
        mock_wf.readframes.return_value = b'\x01\x00' * 10 # Value 1

        mock_wave_open.return_value.__enter__.return_value = mock_wf

        af = AudioFeedback(logger=self.logger, enabled=True)
        data, fs = af._read_wav("dummy.wav")

        self.assertEqual(fs, 44100)
        self.assertEqual(data.dtype, np.int16)
        self.assertEqual(data.shape, (10,))
        self.assertEqual(data[0], 1)

    @patch('chirp.audio_feedback.wave.open')
    def test_read_wav_8bit_stereo(self, mock_wave_open):
        mock_wf = MagicMock()
        mock_wf.getnchannels.return_value = 2
        mock_wf.getframerate.return_value = 22050
        mock_wf.getsampwidth.return_value = 1
        mock_wf.getnframes.return_value = 10
        # 10 frames * 2 channels * 1 byte = 20 bytes
        # Value 128 is "0" in 8-bit PCM (unsigned)
        mock_wf.readframes.return_value = bytes([128] * 20)

        mock_wave_open.return_value.__enter__.return_value = mock_wf

        af = AudioFeedback(logger=self.logger, enabled=True)
        data, fs = af._read_wav("dummy.wav")

        self.assertEqual(fs, 22050)
        self.assertEqual(data.dtype, np.float32)
        # Should be converted to float centered at 0
        self.assertEqual(data[0, 0], 0.0)
        self.assertEqual(data.shape, (10, 2))

    @patch('chirp.audio_feedback.wave.open')
    def test_read_wav_unsupported_width(self, mock_wave_open):
        mock_wf = MagicMock()
        mock_wf.getsampwidth.return_value = 3 # 24-bit not supported in my impl
        mock_wave_open.return_value.__enter__.return_value = mock_wf

        af = AudioFeedback(logger=self.logger, enabled=True)
        with self.assertRaises(ValueError):
            af._read_wav("dummy.wav")

    def test_missing_file_logs_warning(self):
        # We don't mock resources here, so it will try to find the real asset.
        # But we pass an override path that doesn't exist.
        af = AudioFeedback(logger=self.logger, enabled=True)

        with self.assertLogs(self.logger, level='WARNING') as cm:
            af.play_start(override_path="non_existent.wav")

        self.assertTrue(any("Sound file missing" in o for o in cm.output))
        sd.play.assert_not_called()

if __name__ == '__main__':
    unittest.main()
