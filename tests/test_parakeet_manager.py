import os
import sys
import unittest
from unittest.mock import MagicMock
from pathlib import Path

# Mock onnxruntime before importing parakeet_manager
mock_ort = MagicMock()
mock_session_options = MagicMock()
mock_ort.SessionOptions.return_value = mock_session_options
sys.modules["onnxruntime"] = mock_ort

# Mock onnx_asr and onnx_asr.loader
mock_onnx_asr = MagicMock()
sys.modules["onnx_asr"] = mock_onnx_asr

mock_onnx_asr_loader = MagicMock()
sys.modules["onnx_asr.loader"] = mock_onnx_asr_loader

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from chirp.parakeet_manager import ParakeetManager  # noqa: E402

class TestParakeetManager(unittest.TestCase):
    def test_session_options_threads(self):
        """
        Verify that ParakeetManager configures ONNX Runtime session options correctly.
        """
        # Arrange
        threads = 4
        mock_logger = MagicMock()
        mock_path = MagicMock(spec=Path)

        # Act
        _ = ParakeetManager(
            model_name="test-model",
            quantization=None,
            provider_key="cpu",
            threads=threads,
            logger=mock_logger,
            model_dir=mock_path,
        )

        # Assert
        print(f"Intra op threads set to: {mock_session_options.intra_op_num_threads}")
        print(f"Inter op threads set to: {mock_session_options.inter_op_num_threads}")

        self.assertEqual(mock_session_options.intra_op_num_threads, threads)
        self.assertEqual(mock_session_options.inter_op_num_threads, 1)

if __name__ == "__main__":
    unittest.main()
