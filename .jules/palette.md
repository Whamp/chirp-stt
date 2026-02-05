## 2024-05-24 - Persistent CLI Status with Rich
**Learning:** `rich.console.Status` context managers can wrap blocking calls like `keyboard.wait()` to provide a persistent "Ready" state, and updates from worker threads are thread-safe if the same `Status` object is used.
**Action:** Use `with console.status("Ready"): blocking_call()` for CLI apps that need a persistent status line, and update it via `status.update()` from event handlers.
