## 2026-01-22 - Audio Feedback Accessibility
**Learning:** Audio-only feedback for background applications is critical for accessibility, but system-specific libraries like `winsound` limit portability.
**Action:** Encapsulate audio feedback in a robust class that handles platform checks gracefully, and ensure silent failures (logging only) on unsupported platforms to prevent crashes.
