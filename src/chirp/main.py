from __future__ import annotations

import argparse
import concurrent.futures
import logging
import platform
import threading
import time
from typing import Optional, Sequence

import numpy as np

from rich.console import Console
from rich.logging import RichHandler

from .audio_capture import AudioCapture
from .audio_feedback import AudioFeedback
from .config_manager import ConfigManager
from .keyboard_shortcuts import KeyboardShortcutManager
from .logger import get_logger
from .parakeet_manager import ModelNotPreparedError, ParakeetManager
from .text_injector import TextInjector


class ChirpApp:
    def __init__(self, *, verbose: bool = False) -> None:
        level = logging.DEBUG if verbose else logging.INFO
        self.logger = get_logger(level=level)
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()
        model_dir = self.config_manager.model_dir(self.config.parakeet_model, self.config.parakeet_quantization)
        self.logger.debug(
            "Environment: platform=%s python=%s config=%s models=%s",
            platform.platform(),
            platform.python_version(),
            self.config_manager.config_path,
            self.config_manager.models_root,
        )
        self.logger.debug(
            "Config summary: model=%s quantization=%s provider=%s threads=%s paste_mode=%s",
            self.config.parakeet_model,
            self.config.parakeet_quantization or "none",
            self.config.onnx_providers,
            self.config.threads,
            self.config.paste_mode,
        )

        self.keyboard = KeyboardShortcutManager(logger=self.logger)
        self.audio_capture = AudioCapture(status_callback=self._log_capture_status)
        self.audio_feedback = AudioFeedback(
            logger=self.logger,
            enabled=self.config.audio_feedback,
            volume=self.config.audio_feedback_volume,
        )

        console = None
        for handler in self.logger.handlers:
            if isinstance(handler, RichHandler):
                console = handler.console
                break
        if not console:
            console = Console(stderr=True)
        self.console = console

        try:
            with self.console.status("[bold green]Initializing Parakeet model...[/bold green]", spinner="dots"):
                self.parakeet = ParakeetManager(
                    model_name=self.config.parakeet_model,
                    quantization=self.config.parakeet_quantization,
                    provider_key=self.config.onnx_providers,
                    threads=self.config.threads,
                    logger=self.logger,
                    model_dir=model_dir,
                    timeout=self.config.model_timeout,
                )
        except ModelNotPreparedError as exc:
            self.logger.error(str(exc))
            raise SystemExit(1) from exc
        self.text_injector = TextInjector(
            keyboard_manager=self.keyboard,
            logger=self.logger,
            paste_mode=self.config.paste_mode,
            word_overrides=self.config.word_overrides,
            post_processing=self.config.post_processing,
            clipboard_behavior=self.config.clipboard_behavior,
            clipboard_clear_delay=self.config.clipboard_clear_delay,
        )

        self._recording = False
        self._status_indicator = self.console.status("[bold red]Recording...[/bold red]", spinner="dots")
        self._lock = threading.Lock()
        self._stop_timer: Optional[threading.Timer] = None
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="Transcriber")

    def run(self) -> None:
        try:
            self._register_hotkey()
            self.logger.info("Chirp ready. Toggle recording with %s", self.config.primary_shortcut)
            self.keyboard.wait()
        except KeyboardInterrupt:
            self.logger.info("Interrupted, exiting.")

    def _register_hotkey(self) -> None:
        self.logger.debug("Registering hotkey: %s", self.config.primary_shortcut)
        try:
            self.keyboard.register(self.config.primary_shortcut, self.toggle_recording)
        except Exception:
            self.logger.error("Unable to register primary shortcut. Run as Administrator on Windows.")
            raise

    def toggle_recording(self) -> None:
        with self._lock:
            if not self._recording:
                self._start_recording()
            else:
                self._stop_recording()

    def _start_recording(self) -> None:
        self.logger.debug("Starting audio capture")
        try:
            self.audio_capture.start()
        except Exception as exc:
            self.logger.error("Audio capture start failed: %s", exc)
            self.audio_feedback.play_error(self.config.error_sound_path)
            return
        self._recording = True
        self.audio_feedback.play_start(self.config.start_sound_path)
        self.logger.info("Recording started")
        self._status_indicator.start()

        if self.config.max_recording_duration > 0:
            self._stop_timer = threading.Timer(
                self.config.max_recording_duration, self._handle_timeout
            )
            self._stop_timer.start()

    def _handle_timeout(self) -> None:
        self.logger.info("Maximum recording duration reached.")
        self.toggle_recording()

    def _stop_recording(self) -> None:
        if self._stop_timer:
            self._stop_timer.cancel()
            self._stop_timer = None

        self.logger.debug("Stopping audio capture")
        waveform = self.audio_capture.stop()
        self._recording = False
        self._status_indicator.stop()
        self.audio_feedback.play_stop(self.config.stop_sound_path)
        self.logger.info("Recording stopped (%s samples)", waveform.size)
        self._executor.submit(self._transcribe_and_inject, waveform)

    def _transcribe_and_inject(self, waveform) -> None:
        start_time = time.perf_counter()
        if waveform.size == 0:
            self.logger.warning("No audio samples captured")
            return
        try:
            with self.console.status("[bold yellow]Transcribing...[/bold yellow]", spinner="dots"):
                text = self.parakeet.transcribe(waveform, sample_rate=16_000, language=self.config.language)
        except Exception as exc:
            self.logger.exception("Transcription failed: %s", exc)
            self.audio_feedback.play_error(self.config.error_sound_path)
            return
        duration = time.perf_counter() - start_time
        self.logger.debug("Transcription finished in %.2fs (chars=%s)", duration, len(text))
        if not text.strip():
            self.logger.info("Transcription empty; skipping paste")
            return
        self.logger.debug("Transcription: %s", text)
        self.text_injector.inject(text)

    def _log_capture_status(self, message: str) -> None:
        self.logger.debug("Audio status: %s", message)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chirp",
        description="Chirp – Windows dictation app using local Parakeet STT (CPU-only).",
        epilog=(
            "Usage:\n"
            "  uv run python -m chirp.setup   # one-time: download the Parakeet model files\n"
            "  uv run python -m chirp.main    # daily: start Chirp and use the configured hotkey\n\n"
            "While Chirp is running, press your primary shortcut (default: win+alt+d)\n"
            "to toggle recording on and off."
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Smoke-test the pipeline without registering hotkeys or capturing audio",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = _build_parser().parse_args(argv)
    if args.check:
        _run_smoke_check(verbose=args.verbose)
        return
    app = ChirpApp(verbose=args.verbose)
    app.run()


def _run_smoke_check(*, verbose: bool = False) -> None:
    logger = get_logger(level=logging.DEBUG if verbose else logging.INFO)
    logger.info("Running Chirp smoke check")
    config_manager = ConfigManager()
    config = config_manager.load()
    try:
        model_dir = config_manager.model_dir(config.parakeet_model, config.parakeet_quantization)
        parakeet = ParakeetManager(
            model_name=config.parakeet_model,
            quantization=config.parakeet_quantization,
            provider_key=config.onnx_providers,
            threads=config.threads,
            logger=logger,
            model_dir=model_dir,
            timeout=config.model_timeout,
        )
    except ModelNotPreparedError as exc:
        logger.error(str(exc))
        raise SystemExit(1) from exc

    text_injector = TextInjector(
        keyboard_manager=KeyboardShortcutManager(logger=logger),
        logger=logger,
        paste_mode=config.paste_mode,
        word_overrides=config.word_overrides,
        post_processing=config.post_processing,
        clipboard_behavior=False,
        clipboard_clear_delay=config.clipboard_clear_delay,
    )

    dummy_audio = np.zeros(16_000, dtype=np.float32)
    transcription = parakeet.transcribe(dummy_audio, sample_rate=16_000, language=config.language)
    processed = text_injector.process(transcription or "test")
    logger.info("Smoke check passed. Processed sample: %s", processed)


if __name__ == "__main__":
    main()
