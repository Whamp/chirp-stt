## 2025-02-18 - Windows Clipboard Leak in Text Injection
**Vulnerability:** `TextInjector` was unconditionally copying dictated text to the system clipboard before injection, even on Windows where direct keystroke simulation (`keyboard.write`) is used and clipboard is not needed.
**Learning:** Cross-platform abstractions (like "inject text") can lead to platform-specific vulnerabilities if side effects (like clipboard usage) are not conditionally applied. The assumption that "copying to clipboard is harmless" is false for sensitive data.
**Prevention:** Always audit platform-specific implementations of sensitive operations. Ensure side effects are minimized and only applied when strictly necessary for the mechanism to work.
