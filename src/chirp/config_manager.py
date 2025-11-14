from __future__ import annotations

import re
import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSETS_ROOT = PROJECT_ROOT / "src" / "chirp" / "assets"
MODELS_ROOT = ASSETS_ROOT / "models"
CONFIG_PATH = PROJECT_ROOT / "config.toml"


@dataclass(kw_only=True, slots=True)
class ChirpConfig:
    primary_shortcut: str = "ctrl+shift"
    stt_backend: str = "parakeet"
    parakeet_model: str = "nemo-parakeet-tdt-0.6b-v3"
    parakeet_quantization: Optional[str] = None
    onnx_providers: str = "cpu"
    threads: Optional[int] = None
    language: Optional[str] = None
    word_overrides: Dict[str, str] = field(default_factory=dict)
    whisper_prompt: str = ""
    paste_mode: str = "ctrl"
    clipboard_behavior: bool = True
    clipboard_clear_delay: float = 0.75
    audio_feedback: bool = True
    start_sound_path: Optional[str] = None
    stop_sound_path: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChirpConfig":
        merged: Dict[str, Any] = dict(data)
        overrides = merged.get("word_overrides", {}) or {}
        merged["word_overrides"] = {
            str(k).lower(): str(v) for k, v in overrides.items()
        }

        if "primary_shortcut" in merged:
            merged["primary_shortcut"] = str(merged["primary_shortcut"]).lower()
        if "paste_mode" in merged:
            merged["paste_mode"] = str(merged["paste_mode"]).lower()
        if "onnx_providers" in merged:
            merged["onnx_providers"] = str(merged["onnx_providers"]).lower()

        quant = merged.get("parakeet_quantization")
        if quant is not None:
            merged["parakeet_quantization"] = str(quant).lower()

        lang = merged.get("language")
        if lang is not None:
            merged["language"] = str(lang)

        return cls(**merged)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["word_overrides"] = dict(self.word_overrides)
        return payload


class ConfigManager:
    def __init__(self) -> None:
        self._config_path = CONFIG_PATH
        self._models_root = MODELS_ROOT
        self._models_root.mkdir(parents=True, exist_ok=True)

    @property
    def config_path(self) -> Path:
        return self._config_path

    @property
    def models_root(self) -> Path:
        return self._models_root

    def ensure_exists(self) -> None:
        if not self._config_path.exists():
            raise FileNotFoundError(f"Config file not found at {self._config_path}")

    def load(self) -> ChirpConfig:
        self.ensure_exists()
        with self._config_path.open("rb") as handle:
            data = tomllib.load(handle)
        return ChirpConfig.from_dict(data)

    def save(self, config: ChirpConfig) -> None:
        raise NotImplementedError("Saving config.toml is not supported; edit the file manually.")

    def model_dir(self, model_name: str, quantization: Optional[str]) -> Path:
        suffix = "-int8" if (quantization or "").lower() == "int8" else ""
        safe = re.sub(r"[^A-Za-z0-9._-]+", "-", model_name.lower()).strip("-") or "model"
        return self._models_root / f"{safe}{suffix}"

