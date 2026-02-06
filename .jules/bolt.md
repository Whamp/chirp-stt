## 2024-02-18 - Pre-scaled Audio Feedback
**Learning:** AudioFeedback volume scaling was applied during every playback, causing unnecessary numpy overhead and latency.
**Action:** Pre-calculate scaled audio during `_load_and_cache` to minimize `_play_cached` latency (from ~1ms to ~0.04ms).

## 2024-05-22 - Parakeet Model Cold Start
**Learning:** ONNX Runtime initialization and graph optimization cause significant latency (cold start) on the first inference.
**Action:** Implemented `ParakeetManager.warmup()` to run a dummy inference at startup, shifting latency away from the first user interaction.
