## 2025-05-20 - Defense in Depth for Text Injection
**Vulnerability:** Control characters could be injected via `word_overrides` configuration, bypassing initial input sanitization.
**Learning:** Initial input sanitization is insufficient when configuration data (overrides) can re-introduce unsafe characters during processing.
**Prevention:** Implement "Output Sanitization" as a final step in data processing pipelines. Ensure sanitization logic is reusable and safe (e.g., does not unintentionally destroy formatting like trailing whitespace unless intended).
