## 2026-01-18 - Model Output Trust
**Vulnerability:** Unchecked trust in STT model output allowed potential DoS via infinite text generation and control character injection.
**Learning:** Even internal ML models should be treated as untrusted sources when their output drives OS-level actions like keystrokes.
**Prevention:** Sanitize and limit all outputs that bridge the gap from ML inference to OS actions.
## 2026-01-18 - User-Driven Security
**Vulnerability:** Initial DoS fix (text length limit) was replaced by a more user-friendly constraint (recording time limit).
**Learning:** Security controls should align with user workflows. A time limit prevents the 'forgot to toggle off' scenario better than a text limit.
**Prevention:** Implement limits at the source (recording) rather than the sink (injection) when possible.
