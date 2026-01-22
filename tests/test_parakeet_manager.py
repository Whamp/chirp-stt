import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np

from chirp.parakeet_manager import ParakeetManager


class TestParakeetManager(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock()
        self.model_dir = Path("/tmp/dummy_model_dir")

    @patch("chirp.parakeet_manager.onnx_asr")
    @patch("chirp.parakeet_manager.time.time")
    def test_lifecycle(self, mock_time, mock_onnx):
        """Test model load, unload, and reload lifecycle."""
        mock_model_instance = MagicMock()
        mock_onnx.load_model.return_value = mock_model_instance
        mock_time.return_value = 1000.0

        manager = ParakeetManager(
            model_name="test",
            quantization=None,
            provider_key="cpu",
            threads=1,
            logger=self.logger,
            model_dir=self.model_dir,
            timeout=100.0,
        )

        # 1. Verify model is loaded on init
        self.assertIsNotNone(manager._model)
        mock_onnx.load_model.assert_called()
        load_count_initial = mock_onnx.load_model.call_count

        # 2. Unload model manually (simulate timeout)
        mock_time.return_value = 1200.0  # +200s > 100s timeout
        manager._unload_model()
        self.assertIsNone(manager._model)

        # 3. Ensure loaded (reloading)
        manager.ensure_loaded()
        self.assertIsNotNone(manager._model)
        self.assertEqual(mock_onnx.load_model.call_count, load_count_initial + 1)

        # 4. Cleanup
        manager._stop_monitor.set()
        time.sleep(0.05)

    @patch("chirp.parakeet_manager.onnx_asr")
    @patch("chirp.parakeet_manager.time.time")
    def test_transcribe_reloads_and_updates_time(self, mock_time, mock_onnx):
        """Test that transcribe reloads model if unloaded and updates last_access."""
        mock_model_instance = MagicMock()
        mock_model_instance.recognize.return_value = "hello"
        mock_onnx.load_model.return_value = mock_model_instance
        mock_time.return_value = 1000.0

        manager = ParakeetManager(
            model_name="test",
            quantization=None,
            provider_key="cpu",
            threads=1,
            logger=self.logger,
            model_dir=self.model_dir,
            timeout=100.0,
        )

        self.assertEqual(manager._last_access, 1000.0)

        # Unload (simulate timeout)
        mock_time.return_value = 1200.0
        manager._unload_model()
        self.assertIsNone(manager._model)

        # Transcribe should reload
        audio = np.zeros(16000, dtype=np.float32)
        mock_time.return_value = 2000.0
        result = manager.transcribe(audio)

        self.assertEqual(result, "hello")
        self.assertIsNotNone(manager._model)
        self.assertEqual(manager._last_access, 2000.0)

        manager._stop_monitor.set()
        time.sleep(0.05)

    @patch("chirp.parakeet_manager.onnx_asr")
    def test_timeout_zero_disables_monitor(self, mock_onnx):
        """Test that timeout=0 disables the monitor thread."""
        mock_onnx.load_model.return_value = MagicMock()

        manager = ParakeetManager(
            model_name="test",
            quantization=None,
            provider_key="cpu",
            threads=1,
            logger=self.logger,
            model_dir=self.model_dir,
            timeout=0,
        )

        # Monitor thread should not be started
        self.assertIsNone(manager._monitor_thread)
        self.assertIsNotNone(manager._model)


if __name__ == "__main__":
    unittest.main()
