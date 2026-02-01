## 2024-02-18 - Pre-scaled Audio Feedback
**Learning:** AudioFeedback volume scaling was applied during every playback, causing unnecessary numpy overhead and latency.
**Action:** Pre-calculate scaled audio during `_load_and_cache` to minimize `_play_cached` latency (from ~1ms to ~0.04ms).

## 2024-05-22 - Preload Audio Assets
**Learning:** Audio assets (start/stop/error sounds) were loaded lazily on first use, adding I/O latency (tens of ms) to the critical path of the first user interaction.
**Action:** Added `preload_start/stop/error` to `AudioFeedback` and called them during `ChirpApp` initialization. This moves the I/O cost to app startup (where it is masked by model loading) and ensures instant feedback on first hotkey press.
