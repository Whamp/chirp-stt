## 2024-02-18 - Pre-scaled Audio Feedback
**Learning:** AudioFeedback volume scaling was applied during every playback, causing unnecessary numpy overhead and latency.
**Action:** Pre-calculate scaled audio during `_load_and_cache` to minimize `_play_cached` latency (from ~1ms to ~0.04ms).

## 2026-01-29 - Audio Feedback Preloading
**Learning:** Initial audio feedback (e.g. "ping-up.wav") suffered from file I/O latency on the first activation, making the app feel sluggish.
**Action:** Implemented `preload_start/stop/error` in `AudioFeedback` and called them during `ChirpApp` initialization to cache sounds before user interaction.
