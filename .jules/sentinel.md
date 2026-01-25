## 2024-05-23 - Sensitive Data in Logs
**Vulnerability:** Transcribed text was logged at `INFO` level in `ChirpApp`.
**Learning:** Default logging levels (`INFO`) are often used in production or by users. Logging raw input/output (like dictation) at this level exposes sensitive data (passwords, PII) to persistent storage or shared logs.
**Prevention:** Always log user-generated content or sensitive data at `DEBUG` level or lower. Review all `logger.info` calls for potential PII leaks.

## 2025-05-20 - Defense in Depth for Text Injection
**Vulnerability:** Control characters could be injected via `word_overrides` configuration, bypassing initial input sanitization.
**Learning:** Initial input sanitization is insufficient when configuration data (overrides) can re-introduce unsafe characters during processing.
**Prevention:** Implement "Output Sanitization" as a final step in data processing pipelines. Ensure sanitization logic is reusable and safe (e.g., does not unintentionally destroy formatting like trailing whitespace unless intended).
