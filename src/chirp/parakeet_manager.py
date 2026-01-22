from __future__ import annotations

import gc
import logging
import threading
import time
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
        timeout: float = 300.0,
    ) -> None:
        self._logger = logger
        self._model_name = model_name
        self._quantization = quantization
        self._providers = self._resolve_providers(provider_key)
        self._session_options = self._build_session_options(threads)
        self._model_dir = model_dir
        self._timeout = timeout  # 0 or negative means never unload
        self._last_access = time.time()
        self._lock = threading.Lock()
        self._model = self._load_model()
        self._stop_monitor = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None
        if self._timeout > 0:
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()

    def _monitor_loop(self) -> None:
        while not self._stop_monitor.is_set():
            time.sleep(5)
            with self._lock:
                should_unload = (
                    self._model is not None
                    and self._timeout > 0
                    and (time.time() - self._last_access > self._timeout)
                )
            if should_unload:
                self._unload_model()

    def _unload_model(self) -> None:
        with self._lock:
            if self._model is not None and (time.time() - self._last_access > self._timeout):
                self._logger.info("Unloading Parakeet model to free memory.")
                self._model = None
                gc.collect()

    def ensure_loaded(self):
        with self._lock:
            if self._model is None:
                self._logger.info("Reloading Parakeet model...")
                self._model = self._load_model()
            return self._model

    def _resolve_providers(self, key: str) -> Sequence[str]:
        normalized = key.lower()
        if normalized != "cpu":
            self._logger.warning(
                "GPU providers are not supported; forcing CPU provider (received: %s)",
                key,
            )
        return CPU_PROVIDERS

    def _build_session_options(self, threads: Optional[int]):
        if ort is None:
            if threads and threads > 0:
                self._logger.warning("onnxruntime not available; ignoring threads=%s", threads)
            return None

        options = ort.SessionOptions()
        # Optimization: Force inter_op_num_threads to 1.
        # This minimizes overhead for sequential models like Parakeet.
        options.inter_op_num_threads = 1

        if threads and threads > 0:
            options.intra_op_num_threads = threads
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
        with self._lock:
            self._last_access = time.time()
        model = self.ensure_loaded()
        if audio.ndim > 1:
            audio = audio.reshape(-1)
        waveform = audio.astype(np.float32, copy=False)
        if waveform.size == 0:
            return ""
        result = model.recognize(waveform, sample_rate=sample_rate, language=language)
        return result if isinstance(result, str) else str(result)
