## 2024-02-18 - Pre-scaled Audio Feedback
**Learning:** AudioFeedback volume scaling was applied during every playback, causing unnecessary numpy overhead and latency.
**Action:** Pre-calculate scaled audio during `_load_and_cache` to minimize `_play_cached` latency (from ~1ms to ~0.04ms).

## 2024-02-19 - Garbage Collection Lock Contention
**Learning:** `gc.collect()` is a blocking operation that, when held under a thread lock used by foreground tasks, can cause massive latency spikes (e.g. 400ms).
**Action:** Move `gc.collect()` outside critical sections (locks) after setting references to `None`.
