## 2026-01-18 - Model Output Trust
**Vulnerability:** Unchecked trust in STT model output allowed potential DoS via infinite text generation and control character injection.
**Learning:** Even internal ML models should be treated as untrusted sources when their output drives OS-level actions like keystrokes.
**Prevention:** Sanitize and limit all outputs that bridge the gap from ML inference to OS actions.
