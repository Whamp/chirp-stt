## 2024-02-18 - Pre-scaled Audio Feedback
**Learning:** AudioFeedback volume scaling was applied during every playback, causing unnecessary numpy overhead and latency.
**Action:** Pre-calculate scaled audio during `_load_and_cache` to minimize `_play_cached` latency (from ~1ms to ~0.04ms).

## 2026-02-03 - ParakeetManager Lock Contention
**Learning:** `ParakeetManager._unload_model` held the thread lock during `gc.collect()`, potentially blocking concurrent inference requests.
**Action:** Released the lock before invoking garbage collection to minimize the critical section duration.
