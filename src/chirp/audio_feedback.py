from __future__ import annotations

import logging
import platform
import wave
from contextlib import contextmanager, ExitStack
from pathlib import Path
from typing import Dict, Iterator, Optional

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
        self._exit_stack = ExitStack()
        self._cached_paths: Dict[str, Path] = {}
        # Enable if desired AND at least one backend is available
        self._enabled = enabled and (winsound is not None or sd is not None)

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
                if winsound is not None:
                    winsound.PlaySound(override_path, winsound.SND_FILENAME | winsound.SND_ASYNC)  # type: ignore[union-attr]
                elif sd is not None:
                    self._play_with_sounddevice(Path(override_path))
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
        try:
            with self._get_sound_path(asset_name, override_path) as path:
                if winsound is not None:
                    winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)  # type: ignore[union-attr]
                elif sd is not None:
                    self._play_with_sounddevice(path)
        except FileNotFoundError:
            self._logger.warning("Sound file missing: %s", override_path or asset_name)
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.exception("Failed to play sound %s: %s", asset_name, exc)

    def _play_with_sounddevice(self, path: Path) -> None:
        if np is None:
            self._logger.error("numpy not available for sounddevice playback")
            return

        with wave.open(str(path), 'rb') as wf:
            samplerate = wf.getframerate()
            channels = wf.getnchannels()
            frames = wf.readframes(wf.getnframes())
            # Convert buffer to numpy array
            audio_data = np.frombuffer(frames, dtype=np.int16)
            if channels > 1:
                audio_data = audio_data.reshape(-1, channels)

            # sounddevice.play is asynchronous (returns immediately)
            sd.play(audio_data, samplerate)

    @contextmanager
    def _get_sound_path(self, asset_name: str, override_path: Optional[str]) -> Iterator[Path]:
        if override_path:
            yield Path(override_path)
            return

        if asset_name in self._cached_paths:
            yield self._cached_paths[asset_name]
            return

        resource = resources.files("chirp.assets").joinpath(asset_name)
        # Use ExitStack to keep the file context alive for the lifetime of the application
        # (or until AudioFeedback is destroyed, though we don't explicitly close it)
        file_path = self._exit_stack.enter_context(resources.as_file(resource))
        self._cached_paths[asset_name] = file_path
        yield file_path
