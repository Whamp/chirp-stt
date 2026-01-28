## 2026-01-28 - CLI Async Feedback
**Learning:** In CLI apps using `rich`, heavy operations (like inference) running in background threads leave the user guessing if the app is frozen.
**Action:** Use `console.status` context managers inside worker threads to provide "alive" feedback (spinners) without blocking the main UI loop.
