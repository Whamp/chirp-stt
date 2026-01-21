from __future__ import annotations

import logging
import platform
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from importlib import resources

try:
    import winsound  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - non-Windows development
    winsound = None  # type: ignore[assignment]


class AudioFeedback:
    def __init__(self, *, logger: logging.Logger, enabled: bool = True) -> None:
        self._logger = logger
        self._enabled = enabled and winsound is not None

    def play_start(self, override_path: Optional[str] = None) -> None:
        self._play_sound("ping-up.wav", override_path)

    def play_stop(self, override_path: Optional[str] = None) -> None:
        self._play_sound("ping-down.wav", override_path)

    def play_error(self, override_path: Optional[str] = None) -> None:
        if not self._enabled:
            return

        if override_path:
            self._play_sound("error", override_path)
            return

        try:
            winsound.MessageBeep(winsound.MB_ICONHAND)  # type: ignore[union-attr]
        except Exception as exc:
            self._logger.warning("Failed to play error beep: %s", exc)

    def _play_sound(self, asset_name: str, override_path: Optional[str]) -> None:
        if not self._enabled:
            if winsound is None and platform.system() != "Windows":
                self._logger.debug(
                    "Audio feedback disabled: winsound unavailable on %s.",
                    platform.system(),
                )
            return
        try:
            with self._get_sound_path(asset_name, override_path) as path:
                winsound.PlaySound(
                    str(path), winsound.SND_FILENAME | winsound.SND_ASYNC
                )  # type: ignore[union-attr]
        except FileNotFoundError:
            self._logger.warning("Sound file missing: %s", override_path or asset_name)
        except Exception as exc:  # pragma: no cover - defensive
            self._logger.exception("Failed to play sound %s: %s", asset_name, exc)

    @contextmanager
    def _get_sound_path(
        self, asset_name: str, override_path: Optional[str]
    ) -> Iterator[Path]:
        if override_path:
            yield Path(override_path)
            return
        resource = resources.files("chirp.assets").joinpath(asset_name)
        with resources.as_file(resource) as file_path:
            yield file_path
