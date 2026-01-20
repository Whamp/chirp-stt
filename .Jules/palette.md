## 2026-01-20 - Auditory Feedback Gaps
**Learning:** In a headless or background voice application like Chirp, "silence" is ambiguous. It can mean "processing", "listening", or "nothing happened". Users relying on auditory cues were left guessing when transcription failed or returned empty text.
**Action:** Always map backend failure states (and "empty" success states) to distinct auditory feedback, falling back to system sounds (like `MessageBeep` on Windows) to ensure accessibility without requiring custom assets.
