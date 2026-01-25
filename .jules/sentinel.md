## 2024-05-23 - Sensitive Data in Logs
**Vulnerability:** Transcribed text was logged at `INFO` level in `ChirpApp`.
**Learning:** Default logging levels (`INFO`) are often used in production or by users. Logging raw input/output (like dictation) at this level exposes sensitive data (passwords, PII) to persistent storage or shared logs.
**Prevention:** Always log user-generated content or sensitive data at `DEBUG` level or lower. Review all `logger.info` calls for potential PII leaks.
