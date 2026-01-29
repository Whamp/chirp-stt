# Palette's Journal

## 2024-05-23 - Visual Feedback for Long-Running Operations
**Learning:** Users lack confidence when the application performs long-running background tasks (like transcription on CPU) without visual feedback in the CLI. The existing logging is helpful for debugging but insufficient for "alive" status.
**Action:** Implement `rich.console.Status` spinners for all blocking or long-running operations (Transcription, Initialization) to provide immediate, reassuring feedback.
