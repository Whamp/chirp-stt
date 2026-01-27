# Palette's Journal

## 2026-01-27 - Visual Feedback for CLI Async Operations
**Learning:** CLI applications often lack immediate visual feedback for long-running or modal operations (like recording audio or transcribing), leaving users unsure if the app is working.
**Action:** Use `rich.console.Status` (spinners) to provide immediate, persistent visual feedback for active states ("Recording...", "Transcribing...") alongside standard logging. Ensure status indicators are managed (started/stopped) around the blocking or async operations.
