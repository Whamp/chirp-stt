## 2026-01-31 - Visual Feedback for Long-Running CLI Tasks
**Learning:** CLI users often feel uncertain during silent blocking operations (like AI model transcription).
**Action:** Always wrap long-running tasks (>1s) in a `console.status(...)` context manager (using `rich`) to provide immediate visual assurance.
