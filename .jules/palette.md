# Palette's Journal

## 2024-05-23 - Visual Feedback in CLI
**Learning:** Adding a persistent `rich.status.Status` indicator significantly improves perceived responsiveness in CLI apps that perform background tasks (like recording/transcribing).
**Action:** When designing CLI tools with long-running or modal states (recording vs idle), always include a visual indicator of the current mode, ideally with color coding (Red for recording, Green for processing).

## 2024-05-23 - Testing Rich Components
**Learning:** Testing `rich` components (like `Status` or `Console`) often requires checking the *lifecycle* of calls (`start`, `stop`, `update`) rather than just the final state. Also, mocking `RichHandler` requires using the real class or a carefully constructed mock to pass `isinstance` checks.
**Action:** Use `unittest.mock.call` to verify the sequence of UI updates, and instantiate real `RichHandler` objects with mock consoles for integration tests.
