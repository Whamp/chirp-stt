from __future__ import annotations

import logging
import platform
import wave
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple, Union

from importlib import resources

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore[assignment]

try:
    import sounddevice as sd
except (ImportError, OSError):
    sd = None  # type: ignore[assignment]

try:
    import winsound  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - non-Windows development
    winsound = None  # type: ignore[assignment]


class AudioFeedback:
    def __init__(self, *, logger: logging.Logger, enabled: bool = True) -> None:
        self._logger = logger
        # Enable if desired AND at least one backend is available
        self._enabled = enabled and (winsound is not None or sd is not None)
        self._cache: Dict[str, Any] = {}

        if self._enabled:
            backend = "winsound" if winsound is not None else "sounddevice"
            self._logger.debug("Audio feedback initialized using %s", backend)

    def play_start(self, override_path: Optional[str] = None) -> None:
        self._play_sound("ping-up.wav", override_path)

    def play_stop(self, override_path: Optional[str] = None) -> None:
        self._play_sound("ping-down.wav", override_path)

    def play_error(self, override_path: Optional[str] = None) -> None:
        """Play error sound. Uses custom path, or falls back to system beep."""
        if not self._enabled:
            return

        # Try custom sound file first
        if override_path:
            try:
                key = override_path
                if key in self._cache:
                    self._play_cached(self._cache[key])
                else:
                    data = self._load_and_cache(Path(override_path), key)
                    self._play_cached(data)
                return
            except Exception:
                self._logger.warning("Error sound file failed: %s. Falling back to system beep.", override_path)

        # Fall back to system beep
        if winsound is not None:
            try:
                winsound.MessageBeep(winsound.MB_ICONHAND)  # type: ignore[union-attr]
            except Exception as exc:
                self._logger.exception("Failed to play error beep: %s", exc)
        else:
            # No system beep on non-Windows, just log
            self._logger.debug("No error sound available (no winsound, no custom path)")

    def _play_sound(self, asset_name: str, override_path: Optional[str]) -> None:
        if not self._enabled:
            if winsound is None and sd is None and platform.system() != "Windows":
                self._logger.debug("Audio feedback disabled: no audio backend available on %s.", platform.system())
            return

        cache_key = override_path or asset_name
        try:
            if cache_key in self._cache:
                self._play_cached(self._cache[cache_key])
                return

            with self._get_sound_path(asset_name, override_path) as path:
                data = self._load_and_cache(path, cache_key)
                self._play_cached(data)
        except FileNotFoundError:
            self._logger.warning("Sound file missing: %s", override_path or asset_name)
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.exception("Failed to play sound %s: %s", asset_name, exc)

    def _load_and_cache(self, path: Path, key: str) -> Any:
        if winsound is not None:
            with open(path, "rb") as f:
                data = f.read()
            self._cache[key] = data
            return data

        # Fallback to sounddevice
        if np is None:
            self._logger.error("numpy not available for sounddevice playback")
            return None

        with wave.open(str(path), 'rb') as wf:
            samplerate = wf.getframerate()
            channels = wf.getnchannels()
            frames = wf.readframes(wf.getnframes())
            # Convert buffer to numpy array
            audio_data = np.frombuffer(frames, dtype=np.int16)
            if channels > 1:
                audio_data = audio_data.reshape(-1, channels)

            data = (audio_data, samplerate)
            self._cache[key] = data
            return data

    def _play_cached(self, data: Any) -> None:
        if data is None:
            return

        if winsound is not None:
            # winsound.SND_MEMORY = 0x0004
            winsound.PlaySound(data, winsound.SND_MEMORY | winsound.SND_ASYNC)  # type: ignore[union-attr]
        elif sd is not None:
            audio_data, samplerate = data
            sd.play(audio_data, samplerate)

    @contextmanager
    def _get_sound_path(self, asset_name: str, override_path: Optional[str]) -> Iterator[Path]:
        if override_path:
            yield Path(override_path)
            return
        resource = resources.files("chirp.assets").joinpath(asset_name)
        with resources.as_file(resource) as file_path:
            yield file_path
