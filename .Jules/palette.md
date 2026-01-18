# .Jules/palette.md

## 2025-02-18 - Cross-Platform Audio Feedback
**Learning:** `winsound` is strictly Windows-only, but `sounddevice` (which uses PortAudio) handles playback nicely on all platforms if the data is fed as a numpy array.
**Action:** When replacing `winsound` in cross-platform CLI apps, use `wave` (std lib) + `sounddevice` (existing dep) to play simple notification sounds. Be mindful of sample width (8-bit unsigned vs 16-bit signed).
