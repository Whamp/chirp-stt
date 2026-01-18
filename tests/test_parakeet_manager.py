import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import time

# Add src to path
SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.append(str(SRC_DIR))

from chirp.parakeet_manager import ParakeetManager

class TestParakeetManager(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock()
        self.model_dir = Path("dummy_model_dir")

    @patch("chirp.parakeet_manager.onnx_asr")
    @patch("chirp.parakeet_manager.time.time")
    def test_lifecycle(self, mock_time, mock_onnx):
        # Setup mock model
        mock_model_instance = MagicMock()
        mock_onnx.load_model.return_value = mock_model_instance
        mock_time.return_value = 1000.0

        # Initialize manager
        manager = ParakeetManager(
            model_name="test",
            quantization=None,
            provider_key="cpu",
            threads=1,
            logger=self.logger,
            model_dir=self.model_dir,
            timeout=100.0
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
        # Wait a bit for thread to likely exit (not strictly necessary as it's daemon, but cleaner)
        time.sleep(0.1)

    @patch("chirp.parakeet_manager.onnx_asr")
    @patch("chirp.parakeet_manager.time.time")
    def test_transcribe_reloads_and_updates_time(self, mock_time, mock_onnx):
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
            timeout=100.0
        )

        # Verify initial last_access
        self.assertEqual(manager._last_access, 1000.0)

        # Unload (simulate timeout)
        mock_time.return_value = 1200.0
        manager._unload_model()
        self.assertIsNone(manager._model)

        # Transcribe
        import numpy as np
        audio = np.zeros(16000, dtype=np.float32)

        mock_time.return_value = 2000.0
        manager.transcribe(audio)

        # Verify reloaded
        self.assertIsNotNone(manager._model)
        # Verify last_access updated
        self.assertEqual(manager._last_access, 2000.0)

        manager._stop_monitor.set()
        time.sleep(0.1)

if __name__ == "__main__":
    unittest.main()
