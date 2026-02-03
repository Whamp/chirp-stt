## 2024-05-23 - Async Status Indicators
**Learning:** When using `rich.console.Status` in an event-driven app with background threads, simple `start()`/`stop()` calls can cause race conditions. If a background task finishes and calls `stop()` while the main thread has already started a new state (e.g. "Recording..."), the UI breaks.
**Action:** Always guard `status.stop()` in background threads with a state check (e.g. `if not self.active: status.stop()`) to ensure we don't clear a valid, newer status.
