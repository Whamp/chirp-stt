## 2024-02-18 - Pre-scaled Audio Feedback
**Learning:** AudioFeedback volume scaling was applied during every playback, causing unnecessary numpy overhead and latency.
**Action:** Pre-calculate scaled audio during `_load_and_cache` to minimize `_play_cached` latency (from ~1ms to ~0.04ms).

## 2024-05-22 - ONNX Model Warmup
**Learning:** The first inference pass with ONNX Runtime incurs a significant "cold start" penalty (buffer allocation, graph optimization) which impacts user perceived latency for the first dictation.
**Action:** Implemented `ParakeetManager.warmup()` to run a dummy inference during application startup, shifting this cost away from the user interaction loop.
