from __future__ import annotations

import logging
import wave
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional, Tuple

import numpy as np
import sounddevice as sd
from importlib import resources


class AudioFeedback:
    def __init__(self, *, logger: logging.Logger, enabled: bool = True) -> None:
        self._logger = logger
        self._enabled = enabled

    def play_start(self, override_path: Optional[str] = None) -> None:
        self._play_sound("ping-up.wav", override_path)

    def play_stop(self, override_path: Optional[str] = None) -> None:
        self._play_sound("ping-down.wav", override_path)

    def _play_sound(self, asset_name: str, override_path: Optional[str]) -> None:
        if not self._enabled:
            return
        try:
            with self._get_sound_path(asset_name, override_path) as path:
                data, fs = self._read_wav(str(path))
                sd.play(data, fs)
        except FileNotFoundError:
            self._logger.warning("Sound file missing: %s", override_path or asset_name)
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.exception("Failed to play sound %s: %s", asset_name, exc)

    def _read_wav(self, path: str) -> Tuple[np.ndarray, int]:
        """Reads a WAV file and returns (data, samplerate)."""
        with wave.open(path, "rb") as wf:
            channels = wf.getnchannels()
            rate = wf.getframerate()
            width = wf.getsampwidth()
            frames = wf.getnframes()
            buffer = wf.readframes(frames)

            if width == 1:
                # 8-bit audio is unsigned 0-255
                data = np.frombuffer(buffer, dtype=np.uint8)
                # Convert to float32 centered at 0
                data = (data.astype(np.float32) - 128) / 128.0
            elif width == 2:
                # 16-bit is signed
                data = np.frombuffer(buffer, dtype=np.int16)
            elif width == 4:
                # 32-bit is signed
                data = np.frombuffer(buffer, dtype=np.int32)
            else:
                raise ValueError(f"Unsupported sample width: {width}")

            if channels > 1:
                data = data.reshape(-1, channels)

            return data, rate

    @contextmanager
    def _get_sound_path(self, asset_name: str, override_path: Optional[str]) -> Iterator[Path]:
        if override_path:
            yield Path(override_path)
            return
        resource = resources.files("chirp.assets").joinpath(asset_name)
        with resources.as_file(resource) as file_path:
            yield file_path
