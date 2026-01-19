import unittest
from pathlib import Path
from src.chirp.config_manager import ConfigManager

class TestSecurity(unittest.TestCase):
    def test_model_dir_path_traversal(self):
        """Verify that model_dir prevents path traversal."""
        # Mock ConfigManager to avoid file system dependency on config.toml
        # We only need _models_root for this test
        cm = ConfigManager()
        # Ensure we don't try to load config.toml which might not exist or fail
        cm._config_path = Path("/tmp/nonexistent_config.toml")
        cm._models_root = Path("/tmp/models")

        # Test case: ".."
        path = cm.model_dir("..", None)
        # Should resolve to "model" inside models_root
        expected = cm.models_root / "model"
        self.assertEqual(path, expected, "Traveral via '..' failed")

        # Test case: "my..model"
        path = cm.model_dir("my..model", None)
        # Should resolve to "my.model"
        expected = cm.models_root / "my.model"
        self.assertEqual(path, expected, "Dots were not collapsed")

        # Test case: "safe"
        path = cm.model_dir("safe", None)
        expected = cm.models_root / "safe"
        self.assertEqual(path, expected)

if __name__ == '__main__':
    unittest.main()
