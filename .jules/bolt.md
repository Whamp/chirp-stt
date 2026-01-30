## 2024-02-18 - Pre-scaled Audio Feedback
**Learning:** AudioFeedback volume scaling was applied during every playback, causing unnecessary numpy overhead and latency.
**Action:** Pre-calculate scaled audio during `_load_and_cache` to minimize `_play_cached` latency (from ~1ms to ~0.04ms).

## 2026-01-30 - Lock Contention with GC
**Learning:** `gc.collect()` inside a thread lock blocks all other threads needing that lock, causing potential latency spikes during model unloading.
**Action:** Move `gc.collect()` outside critical sections (locks) whenever possible, using flags to signal the need for collection.
