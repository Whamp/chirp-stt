## 2024-02-18 - Pre-scaled Audio Feedback
**Learning:** AudioFeedback volume scaling was applied during every playback, causing unnecessary numpy overhead and latency.
**Action:** Pre-calculate scaled audio during `_load_and_cache` to minimize `_play_cached` latency (from ~1ms to ~0.04ms).

## 2024-02-18 - Lock Contention in Model Unloading
**Learning:** `ParakeetManager._unload_model` executed `gc.collect()` inside the thread lock, potentially blocking transcription requests for hundreds of milliseconds during cleanup.
**Action:** Move `gc.collect()` outside the critical section to allow concurrent lock acquisition by other threads.
