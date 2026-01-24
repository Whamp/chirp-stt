## 2025-02-18 - CLI Async Feedback
**Learning:** Users of CLI applications lack visibility into background thread operations (like model inference), leading to uncertainty about application state.
**Action:** When delegating long-running tasks to background threads (e.g., `ThreadPoolExecutor`), always ensure the main thread's console displays a dynamic status indicator (like a spinner) to confirm activity.
