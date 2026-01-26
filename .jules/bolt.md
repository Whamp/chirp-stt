## 2024-02-18 - Pre-scaled Audio Feedback
**Learning:** AudioFeedback volume scaling was applied during every playback, causing unnecessary numpy overhead and latency.
**Action:** Pre-calculate scaled audio during `_load_and_cache` to minimize `_play_cached` latency (from ~1ms to ~0.04ms).

## 2024-05-23 - GC Latency in Locks
**Learning:** Calling `gc.collect()` inside a lock blocks all other threads waiting for that lock, potentially causing UI hiccups or transcription delays.
**Action:** Move `gc.collect()` outside the critical section (lock) when unloading models.
