import unittest
from unittest.mock import MagicMock, patch
import time
import threading
from pathlib import Path

# Mocking modules before import if necessary, but unittest.mock.patch handles it better usually.
# However, for type checking imports inside the file, we might need to be careful.

from chirp.parakeet_manager import ParakeetManager

class TestGCOptimization(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock()
        self.mock_model_dir = MagicMock(spec=Path)
        self.mock_model_dir.mkdir.return_value = None

    @patch("chirp.parakeet_manager.gc")
    @patch("chirp.parakeet_manager.onnx_asr")
    @patch("chirp.parakeet_manager.ort")
    def test_unload_model_gc_outside_lock(self, mock_ort, mock_onnx_asr, mock_gc):
        """
        Verifies that gc.collect() is called and that it is called
        when the lock is NOT held.
        """
        # Setup
        mock_model = MagicMock()
        mock_onnx_asr.load_model.return_value = mock_model

        manager = ParakeetManager(
            model_name="test_model",
            quantization=None,
            provider_key="cpu",
            threads=1,
            logger=self.mock_logger,
            model_dir=self.mock_model_dir,
            timeout=1.0
        )

        # Ensure loaded
        manager.ensure_loaded()
        self.assertIsNotNone(manager._model)

        # Simulate timeout
        manager._last_access = time.time() - 2.0

        # Replace the lock with a real lock that we can inspect
        lock = threading.Lock()
        manager._lock = lock

        # Define a side effect for gc.collect that checks if lock is locked
        def gc_side_effect():
            if lock.locked():
                raise RuntimeError("gc.collect() called while lock is held!")

        mock_gc.collect.side_effect = gc_side_effect

        # Attempt to unload
        # In the unoptimized code, this should raise RuntimeError.
        # In the optimized code, it should succeed.

        try:
            manager._unload_model()
        except RuntimeError as e:
            if "gc.collect() called while lock is held!" in str(e):
                self.fail("Performance Regression: gc.collect() is being called inside the lock!")
            raise e

        # Verify gc was called
        mock_gc.collect.assert_called_once()
        self.assertIsNone(manager._model)

if __name__ == "__main__":
    unittest.main()
