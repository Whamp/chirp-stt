## 2024-05-22 - Unnecessary Clipboard Overwrite on Windows
**Vulnerability:** `TextInjector` unconditionally copied text to clipboard before checking platform, causing clipboard overwrite on Windows where direct typing is used. This exposed sensitive dictated text to clipboard history and overwrote user's clipboard content.
**Learning:** Logic intended to be platform-specific (direct typing vs paste) was partially defeated by common setup code (clipboard copy) running unconditionally before the platform check.
**Prevention:** Guard all platform-specific operations, including their preparation steps. Use early returns for distinct platform strategies.
