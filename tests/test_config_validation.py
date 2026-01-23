import unittest

from chirp.config_manager import ChirpConfig


class TestConfigValidation(unittest.TestCase):
    def test_validate_threads_negative(self):
        """Negative threads should fail validation."""
        conf = ChirpConfig(threads=-1)
        with self.assertRaisesRegex(ValueError, "threads must be non-negative"):
            conf.validate()

    def test_validate_clipboard_delay_negative(self):
        """Non-positive clipboard_clear_delay should fail validation."""
        conf = ChirpConfig(clipboard_clear_delay=-1.0)
        with self.assertRaisesRegex(ValueError, "clipboard_clear_delay must be positive"):
            conf.validate()

    def test_validate_clipboard_delay_zero(self):
        """Zero clipboard_clear_delay should fail validation."""
        conf = ChirpConfig(clipboard_clear_delay=0)
        with self.assertRaisesRegex(ValueError, "clipboard_clear_delay must be positive"):
            conf.validate()

    def test_validate_paste_mode_invalid(self):
        """Invalid paste_mode should fail validation."""
        conf = ChirpConfig(paste_mode="hacking")
        with self.assertRaisesRegex(ValueError, r"paste_mode must be 'ctrl' or 'ctrl\+shift'"):
            conf.validate()

    def test_validate_model_timeout_negative(self):
        """Negative model_timeout should fail validation."""
        conf = ChirpConfig(model_timeout=-1.0)
        with self.assertRaisesRegex(ValueError, "model_timeout must be non-negative"):
            conf.validate()

    def test_validate_max_recording_duration_negative(self):
        """Negative max_recording_duration should fail validation."""
        conf = ChirpConfig(max_recording_duration=-1.0)
        with self.assertRaisesRegex(ValueError, "max_recording_duration must be non-negative"):
            conf.validate()

    def test_validate_max_recording_duration_excessive(self):
        """Excessive max_recording_duration should fail validation (DoS prevention)."""
        conf = ChirpConfig(max_recording_duration=7201.0)
        with self.assertRaisesRegex(ValueError, "max_recording_duration must be <="):
            conf.validate()

    def test_validate_sound_path_missing(self):
        """Non-existent sound paths should fail validation."""
        conf = ChirpConfig(start_sound_path="/this/path/absolutely/should/not/exist.wav")
        with self.assertRaisesRegex(ValueError, "start_sound_path does not exist"):
            conf.validate()

        conf = ChirpConfig(stop_sound_path="/this/path/absolutely/should/not/exist.wav")
        with self.assertRaisesRegex(ValueError, "stop_sound_path does not exist"):
            conf.validate()

    def test_valid_default_config(self):
        """Default config should pass validation."""
        conf = ChirpConfig()
        conf.validate()  # Should not raise

    def test_valid_config_with_zero_timeouts(self):
        """Zero timeouts (disable) should pass validation."""
        conf = ChirpConfig(model_timeout=0, max_recording_duration=0)
        conf.validate()  # Should not raise

    def test_from_dict_then_validate(self):
        """Verify the flow used by ConfigManager (from_dict -> validate)."""
        data = {"threads": -5, "paste_mode": "Hack"}
        conf = ChirpConfig.from_dict(data)
        # from_dict converts "Hack" to "hack"
        self.assertEqual(conf.paste_mode, "hack")

        with self.assertRaisesRegex(ValueError, "threads must be non-negative"):
            conf.validate()

        conf.threads = 1  # fix threads
        with self.assertRaisesRegex(ValueError, r"paste_mode must be 'ctrl' or 'ctrl\+shift'"):
            conf.validate()


if __name__ == "__main__":
    unittest.main()
