from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import onnx_asr
from onnx_asr.loader import ModelFileNotFoundError, ModelPathNotFoundError

try:
    import onnxruntime as ort
except ImportError:  # pragma: no cover - optional dependency
    ort = None  # type: ignore[assignment]


CPU_PROVIDERS: Sequence[str] = ("CPUExecutionProvider",)


class ModelNotPreparedError(RuntimeError):
    pass


class ParakeetManager:
    def __init__(
        self,
        *,
        model_name: str,
        quantization: Optional[str],
        provider_key: str,
        threads: Optional[int],
        logger: logging.Logger,
        model_dir: Path,
    ) -> None:
        self._logger = logger
        self._model_name = model_name
        self._quantization = quantization
        self._providers = self._resolve_providers(provider_key)
        self._session_options = self._build_session_options(threads)
        self._model_dir = model_dir
        self._model = self._load_model()

    def _resolve_providers(self, key: str) -> Sequence[str]:
        normalized = key.lower()
        if normalized != "cpu":
            self._logger.warning(
                "GPU providers are not supported; forcing CPU provider (received: %s)",
                key,
            )
        return CPU_PROVIDERS

    def _build_session_options(self, threads: Optional[int]):
        if not threads or threads < 1:
            return None
        if ort is None:
            self._logger.warning("onnxruntime not available; ignoring threads=%s", threads)
            return None
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        # Force inter-op threads to 1 for sequential execution (Parakeet V3)
        # Setting this > 1 adds overhead without benefit for batch_size=1 inference
        options.inter_op_num_threads = 1
        return options

    def _load_model(self):
        self._logger.info(
            "Loading Parakeet model %s (quantization=%s, providers=%s)",
            self._model_name,
            self._quantization or "none",
            ",".join(self._providers),
        )
        self._model_dir.mkdir(parents=True, exist_ok=True)
        try:
            return onnx_asr.load_model(
                self._model_name,
                path=str(self._model_dir),
                quantization=self._quantization,
                providers=self._providers,
                sess_options=self._session_options,
            )
        except (ModelPathNotFoundError, ModelFileNotFoundError) as exc:
            raise ModelNotPreparedError(
                f"Model not found at {self._model_dir} — run: uv run chirp-setup"
            ) from exc

    def transcribe(self, audio: np.ndarray, *, sample_rate: int = 16_000, language: Optional[str] = None) -> str:
        if audio.ndim > 1:
            audio = audio.reshape(-1)
        waveform = audio.astype(np.float32, copy=False)
        if waveform.size == 0:
            return ""
        result = self._model.recognize(waveform, sample_rate=sample_rate, language=language)
        return result if isinstance(result, str) else str(result)
