# Chirp

Chirp is a Windows dictation app that runs fully locally using ParakeetV3 STT and is managed end-to-end with `uv`. Chirp does not require the ability to run executable files (like .exe) on Windows. It was designed so that if you're allowed to run Python on your machine, you can run Chirp. 

## Why ParakeetV3? 

ParakeetV3 has indistinguishable accuracy from Whisper-large-V3 (multilingual WER 4.91 vs 5.05) but is 17x faster and only requires a CPU while Whisper models of comparable accuracy require GPU's. 

https://huggingface.co/spaces/hf-audio/open_asr_leaderboard

## Goals
- Provide fast, reliable, local-first dictation on Windows.
- GPU not needed or wanted.
- Corporate environment friendly - NO NEW EXECUTABLES (.exe) REQUIRED. If you can run python you can run chirp.

## Features
- Local STT via Parakeet TDT 0.6B v3 with optional int8 quantization.
- Global hotkey to toggle capture, clipboard paste injection, and configurable word overrides.
- Optional audio feedback cues and style prompting for post-processed text.
- CPU support by default with optional GPU providers when available.

## Architecture
- `src/chirp/main.py` — CLI entrypoint and application loop.
- `src/chirp/config_manager.py` — configuration loading and Windows-specific paths.
- `src/chirp/parakeet_manager.py` — Parakeet backend integration and provider handling.
- `src/chirp/setup.py` — one-time setup routine that prepares local model assets.

## Setup (Windows, uv-only)
1. Clone the repository and enter it:
   ```powershell
   git clone https://github.com/Whamp/chirp.git
   cd chirp
   uv run python -m chirp.setup #one-time setup and model downloading
   ```
   
## Running
- Daily usage (preferred, works even on systems that block `.exe` launchers):
  ```powershell
  uv run python -m chirp.main
  ```
- Verbose/debug logging:
  ```powershell
  uv run python -m chirp.main -- --verbose
  ```
- CLI help and options:
  ```powershell
  uv run python -m chirp.main -- --help
  ```
## Customization

- The config.toml has sensible defaults but is fully customizable.
- config.toml also allows for word_overrides ie. parra keet -> parakeet
  config.toml:
```
primary_shortcut = "ctrl+shift"                 # Hotkey that toggles recording; any combination supported by the `keyboard` library works (e.g. "ctrl+shift+space").
stt_backend = "parakeet"                        # Only "parakeet" is bundled today, but keeping this key lets us add more backends later if needed.
parakeet_model = "nemo-parakeet-tdt-0.6b-v3"    # Deployed ONNX bundle name; keep as-is unless new models are added.
parakeet_quantization = ""                      # Set to "int8" to download/use the quantized model variant; leave blank for default fp16.
onnx_providers = "cpu"                          # ONNX runtime provider string (comma- or pipe-separated if your build supports multiple providers, e.g. "cuda" or "cpu|dml").
threads = 0                                     # 0 (or empty) lets ONNX decide; set a positive integer to pin thread usage.
language = "en"                                 # Optional ISO language code; leave blank to let Parakeet auto-detect.
post_processing = ""                            # Text prompt for the StyleGuide; see docs/post_processing_style_guide.md (e.g. "sentence case", "prepend: >>", "append: — dictated with Chirp").
paste_mode = "ctrl"                             # Non-Windows platforms honor this: "ctrl" -> Ctrl+V, "ctrl+shift" -> Ctrl+Shift+V. Windows types text directly today.
clipboard_behavior = true                       # Keeps clipboard history clean when true by clearing it after `clipboard_clear_delay` seconds.
clipboard_clear_delay = 0.75                    # Seconds to wait before clearing the clipboard (only if `clipboard_behavior` is true).
audio_feedback = true                           # Enables start/stop chime playback.
start_sound_path = ""                           # Leave blank to use bundled asset; default: src/chirp/assets/ping-up.wav
stop_sound_path = ""                            # Leave blank to use bundled asset; default: src/chirp/assets/ping-down.wav

# Word overrides map spoken tokens (case-insensitive) to replacement text.
[word_overrides]
parrakeat = "parakeet"
"parra keat" = "parakeet"  
```

## Removal
- Delete the cloned `chirp` directory.
- That's it. 

### Acknowledgments

- NVIDA - https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3
- Ilya Stupakov - https://huggingface.co/istupakov/parakeet-tdt-0.6b-v3-onnx
