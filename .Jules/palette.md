# Palette's Journal

## 2026-01-23 - Rich Spinners for CLI feedback
**Learning:** In CLI apps using `rich` logging, long blocking operations (like model loading) feel unresponsive. Wrapping them in a `console.status` spinner provides immediate "aliveness" feedback. Reusing the logger's console prevents output conflicts.
**Action:** Always check for `RichHandler` to reuse the console when adding visual elements to `ChirpApp`.
