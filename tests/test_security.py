import unittest
from pathlib import Path
from chirp.config_manager import ConfigManager


class TestSecurity(unittest.TestCase):
    def setUp(self):
        """Set up a ConfigManager with a mock models_root."""
        self.cm = ConfigManager()
        self.cm._config_path = Path("/tmp/nonexistent_config.toml")
        self.cm._models_root = Path("/tmp/models")

    def test_model_dir_double_dot_traversal(self):
        """Verify that '..' resolves to safe 'model' fallback."""
        path = self.cm.model_dir("..", None)
        expected = self.cm.models_root.resolve() / "model"
        self.assertEqual(path, expected)

    def test_model_dir_collapses_multiple_dots(self):
        """Verify that 'my..model' collapses to 'my.model'."""
        path = self.cm.model_dir("my..model", None)
        expected = self.cm.models_root.resolve() / "my.model"
        self.assertEqual(path, expected)

    def test_model_dir_safe_name(self):
        """Verify that a safe name works correctly."""
        path = self.cm.model_dir("safe", None)
        expected = self.cm.models_root.resolve() / "safe"
        self.assertEqual(path, expected)

    def test_model_dir_with_quantization(self):
        """Verify that int8 suffix is appended correctly."""
        path = self.cm.model_dir("mymodel", "int8")
        expected = self.cm.models_root.resolve() / "mymodel-int8"
        self.assertEqual(path, expected)

    def test_model_dir_empty_falls_back(self):
        """Verify that empty/whitespace model names fall back to 'model'."""
        path = self.cm.model_dir("", None)
        expected = self.cm.models_root.resolve() / "model"
        self.assertEqual(path, expected)

    def test_model_dir_dots_only_falls_back(self):
        """Verify that '...' falls back to 'model'."""
        path = self.cm.model_dir("...", None)
        expected = self.cm.models_root.resolve() / "model"
        self.assertEqual(path, expected)


if __name__ == "__main__":
    unittest.main()
