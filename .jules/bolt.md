## 2024-02-18 - Pre-scaled Audio Feedback
**Learning:** AudioFeedback volume scaling was applied during every playback, causing unnecessary numpy overhead and latency.
**Action:** Pre-calculate scaled audio during `_load_and_cache` to minimize `_play_cached` latency (from ~1ms to ~0.04ms).

## 2026-01-28 - Non-blocking GC for Model Unloading
**Learning:** `gc.collect()` was called inside `ParakeetManager`'s lock, causing ~400ms latency spikes for inference requests if they coincided with model unload events.
**Action:** Move `gc.collect()` outside the lock using a local flag. This reduces lock contention to ~0ms, allowing concurrent threads to reload the model immediately while GC runs in the background.
