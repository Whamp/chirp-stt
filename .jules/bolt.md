## 2024-05-22 - Audio Feedback Latency
**Learning:** `AudioFeedback` was reloading WAV files from disk on every `play_start`/`play_stop` call, causing unnecessary I/O latency on the UI thread.
**Action:** Implemented in-memory caching for audio assets. Future audio features should also cache assets if reused frequently.
