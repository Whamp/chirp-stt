## 2024-05-23 - Sensitive Data in Logs
**Vulnerability:** Transcribed text was logged at `INFO` level in `ChirpApp`.
**Learning:** Default logging levels (`INFO`) are often used in production or by users. Logging raw input/output (like dictation) at this level exposes sensitive data (passwords, PII) to persistent storage or shared logs.
**Prevention:** Always log user-generated content or sensitive data at `DEBUG` level or lower. Review all `logger.info` calls for potential PII leaks.

## 2025-05-20 - Defense in Depth for Text Injection
**Vulnerability:** Control characters could be injected via `word_overrides` configuration, bypassing initial input sanitization.
**Learning:** Initial input sanitization is insufficient when configuration data (overrides) can re-introduce unsafe characters during processing.
**Prevention:** Implement "Output Sanitization" as a final step in data processing pipelines. Ensure sanitization logic is reusable and safe (e.g., does not unintentionally destroy formatting like trailing whitespace unless intended).

## 2025-05-21 - Unbounded File Read in AudioFeedback
**Vulnerability:** `AudioFeedback._load_and_cache` read entire audio files into memory without size limits, allowing potential DoS via memory exhaustion if a user (or attacker via config) pointed to a very large file.
**Learning:** Loading external assets (even local ones) based on configuration requires validation of resource limits (size, type) to prevent resource exhaustion. Implicit trust in local file paths is risky if configuration can be shared or modified.
**Prevention:** Enforce strict file size limits (e.g., 5MB) before reading files into memory. Use `path.stat().st_size` for a cheap pre-check.
