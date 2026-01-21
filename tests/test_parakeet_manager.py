import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Ensure src is in path for imports
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from chirp.parakeet_manager import ParakeetManager

class TestParakeetManager(unittest.TestCase):
    def setUp(self):
        self.logger = MagicMock()
        self.model_dir = Path("/tmp/mock_models")

    @patch("chirp.parakeet_manager.onnx_asr")
    def test_session_options_threading(self, mock_onnx_asr):
        # Mock load_model
        mock_onnx_asr.load_model.return_value = MagicMock()

        # Initialize with threads=4
        _ = ParakeetManager(
            model_name="test_model",
            quantization=None,
            provider_key="cpu",
            threads=4,
            logger=self.logger,
            model_dir=self.model_dir
        )

        # Check load_model call
        args, kwargs = mock_onnx_asr.load_model.call_args
        sess_options = kwargs.get('sess_options')

        self.assertIsNotNone(sess_options)
        self.assertEqual(sess_options.intra_op_num_threads, 4)
        self.assertEqual(sess_options.inter_op_num_threads, 1)

    @patch("chirp.parakeet_manager.onnx_asr")
    def test_session_options_default(self, mock_onnx_asr):
        mock_onnx_asr.load_model.return_value = MagicMock()

        # Initialize with threads=None
        _ = ParakeetManager(
            model_name="test_model",
            quantization=None,
            provider_key="cpu",
            threads=None,
            logger=self.logger,
            model_dir=self.model_dir
        )

        args, kwargs = mock_onnx_asr.load_model.call_args
        sess_options = kwargs.get('sess_options')

        # Should be None to let ONNX decide
        self.assertIsNone(sess_options)

if __name__ == "__main__":
    unittest.main()
