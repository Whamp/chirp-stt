## 2024-02-18 - Pre-scaled Audio Feedback
**Learning:** AudioFeedback volume scaling was applied during every playback, causing unnecessary numpy overhead and latency.
**Action:** Pre-calculate scaled audio during `_load_and_cache` to minimize `_play_cached` latency (from ~1ms to ~0.04ms).

## 2025-05-18 - Unlocked Garbage Collection
**Learning:** `ParakeetManager` held the model lock during `gc.collect()`, forcing concurrent `transcribe` requests (which require the lock) to wait for full GC completion before they could even *start* reloading the model.
**Action:** Release the lock before calling `gc.collect()`. This allows `transcribe` to acquire the lock and begin `load_model` (which releases GIL for C++ ops) in parallel with the garbage collection of the old model.
