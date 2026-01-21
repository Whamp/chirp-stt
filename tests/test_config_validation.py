import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from chirp.config_manager import ChirpConfig

class TestConfigValidation(unittest.TestCase):
    def test_validate_threads(self):
        conf = ChirpConfig(threads=-1)
        with self.assertRaisesRegex(ValueError, "threads must be non-negative"):
            conf.validate()

    def test_validate_clipboard_delay(self):
        conf = ChirpConfig(clipboard_clear_delay=-1.0)
        with self.assertRaisesRegex(ValueError, "clipboard_clear_delay must be positive"):
            conf.validate()

    def test_validate_paste_mode(self):
        conf = ChirpConfig(paste_mode="hacking")
        # Escape + in regex
        with self.assertRaisesRegex(ValueError, r"paste_mode must be 'ctrl' or 'ctrl\+shift'"):
            conf.validate()

    def test_validate_sound_paths(self):
        conf = ChirpConfig(start_sound_path="/this/path/absolutely/should/not/exist.wav")
        with self.assertRaisesRegex(ValueError, "start_sound_path does not exist"):
            conf.validate()

        conf = ChirpConfig(stop_sound_path="/this/path/absolutely/should/not/exist.wav")
        with self.assertRaisesRegex(ValueError, "stop_sound_path does not exist"):
            conf.validate()

    def test_valid_config(self):
        """Ensure default/valid config passes validation."""
        conf = ChirpConfig()
        try:
            conf.validate()
        except ValueError as e:
            self.fail(f"validate() raised ValueError unexpectedly for default config: {e}")

    def test_from_dict_workflow(self):
        """Verify the flow used by ConfigManager (from_dict -> validate)"""
        data = {"threads": -5, "paste_mode": "Hack"}
        conf = ChirpConfig.from_dict(data)
        # from_dict converts "Hack" to "hack"
        self.assertEqual(conf.paste_mode, "hack")

        with self.assertRaisesRegex(ValueError, "threads must be non-negative"):
            conf.validate()

        conf.threads = 1 # fix threads
        with self.assertRaisesRegex(ValueError, r"paste_mode must be 'ctrl' or 'ctrl\+shift'"):
            conf.validate()

if __name__ == "__main__":
    unittest.main()
