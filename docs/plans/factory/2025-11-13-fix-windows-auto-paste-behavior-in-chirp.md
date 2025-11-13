## Summary of the issue
- Current behavior: On Windows, when recording is toggled off and transcription completes, the text is:
  - Logged to the CLI (`ChirpApp._transcribe_and_inject` logs `Transcription: ...`).
  - Copied to the clipboard via `pyperclip.copy()` in `TextInjector.inject`.
  - **But** it is not auto-pasted into the currently focused window, even though no error is logged.
- Existing implementation:
  - `TextInjector.inject` copies the processed text to the clipboard, sleeps 0.12s, then calls `KeyboardShortcutManager.send(combo)` where `combo` is `"ctrl+v"` or `"ctrl+shift+v"` depending on `paste_mode`.
  - `KeyboardShortcutManager.send` is a thin wrapper around `keyboard.send(combination)`.
- Likely problem: On your Windows setup, `keyboard.send()` is not successfully generating a paste keystroke into the active window (often a known fragility of global key injection on Windows), even though clipboard writes succeed. The code has no fallback, so you see only clipboard updates + logging.

---

## Design goals
1. **Guarantee default auto-paste on Windows** whenever transcription succeeds and produces non-empty text.
2. **Keep clipboard behavior unchanged**: the text must still go to the clipboard and obey `clipboard_behavior` / `clipboard_clear_delay`.
3. **Minimize scope and risk**: touch as few modules as possible (`text_injector.py`, `keyboard_shortcuts.py`), avoid new dependencies, and preserve current behavior on non-Windows platforms.
4. **Preserve configurability**: keep `paste_mode` meaningful and backwards-compatible for users who might have customized it.

---

## Proposed implementation

### 1. Make keyboard injection more explicit and platform-aware

**Files touched**:
- `src/chirp/keyboard_shortcuts.py`
- `src/chirp/text_injector.py`

#### 1.1 Extend `KeyboardShortcutManager` with a `write` helper

Add a small wrapper around `keyboard.write` so `TextInjector` doesn’t depend directly on the third-party API:

```python
# src/chirp/keyboard_shortcuts.py

class KeyboardShortcutManager:
    def __init__(self, *, logger: logging.Logger) -> None:
        self._logger = logger

    def register(self, shortcut: str, callback: Callable[[], None]) -> None:
        ...  # unchanged

    def send(self, combination: str) -> None:
        keyboard.send(combination)

    def write(self, text: str) -> None:
        """Type text at the active cursor position using the OS keyboard layer."""
        keyboard.write(text)

    def wait(self) -> None:
        keyboard.wait()
```

This gives us a second injection primitive that types the text directly, instead of relying on a paste hotkey.

#### 1.2 Make `TextInjector.inject` platform-aware and add a robust Windows path

Update `TextInjector.inject` to:

- Always copy to clipboard as it does now (for consistency and manual re-use).
- Use **typing-based injection on Windows by default**, which is empirically more reliable than sending `Ctrl+V` globally.
- Keep the current `paste_mode` keystroke-based behavior for non-Windows platforms to avoid surprising changes.

Concretely:

```python
# src/chirp/text_injector.py
+ import sys

class TextInjector:
    ...
    def inject(self, text: str) -> None:
        processed = self.process(text)
        try:
            pyperclip.copy(processed)
        except pyperclip.PyperclipException as exc:
            self._logger.error("Clipboard copy failed: %s", exc)
            return

        # Small delay so the clipboard update is visible to most targets
        time.sleep(0.12)

-       combo = "ctrl+v" if self._paste_mode == "ctrl" else "ctrl+shift+v"
-       try:
-           self._keyboard.send(combo)
-       except Exception as exc:  # pragma: no cover - runtime safety
-           self._logger.error("Paste injection failed: %s", exc)
+       try:
+           if sys.platform.startswith("win"):
+               # On Windows, directly type the text at the active caret position.
+               # This avoids relying on Ctrl+V working globally in all contexts.
+               self._keyboard.write(processed)
+           else:
+               # Preserve existing semantics elsewhere: send a paste hotkey.
+               combo = "ctrl+v" if self._paste_mode == "ctrl" else "ctrl+shift+v"
+               self._keyboard.send(combo)
+       except Exception as exc:  # pragma: no cover - runtime safety
+           self._logger.error("Paste injection failed: %s", exc)

        if self._clipboard_behavior:
            self._schedule_clipboard_clear()
```

**Behavioral changes:**
- **Windows (your use case):** after transcription, text is copied to clipboard and then physically typed into the active window. This should reliably satisfy the “auto-paste” expectation even when `keyboard.send("ctrl+v")` is unreliable.
- **Non-Windows:** behavior remains effectively the same as today — copy to clipboard and send a paste hotkey based on `paste_mode`.
- `paste_mode` still matters outside Windows; on Windows, it effectively becomes a no-op (we can later extend to support a pure `"ctrl"`/`"ctrl+shift"` mode again if needed).


### 2. Optional: add more informative logging (minimal and only on failures)

To keep logs minimal but useful, we will:
- Keep existing debug/info logs in `main.py` as-is.
- Rely on the existing error log in `TextInjector.inject` for paste failures; no extra logging is added except for the new branch we already log on exception.

This respects your “minimal comments/logs” preference while still providing a clear signal if the new injection path ever raises.

---

## Validation plan

Because this is heavily OS-integrated behavior, we’ll rely on a mix of **manual validation on Windows** and **lightweight automated checks**.

### 2.1 Automated checks (run under `uv` or plain Python)

After implementing changes, we’ll run:

1. **Import and syntax checks** to ensure everything compiles:
   - `uv run python -m compileall src` (or `python -m compileall src` in your environment).

2. **Smoke check of CLI wiring** (no recording, just make sure the app starts):
   - `uv run chirp --help`

No existing tests are present in the repo, so we’ll avoid introducing a full test suite unless you ask for it. We will, however, keep the changes trivial and local to minimize risk.

### 2.2 Manual validation on Windows (primary verification)

After installing the updated package or running the app from source:

1. **Baseline hotkey and recording behavior**
   - Start `uv run chirp` from a terminal.
   - Focus a text target such as Notepad or any text box.
   - Press the configured `primary_shortcut` (default `win+alt+d`) to start recording.
   - Speak a short sentence, then press the shortcut again to stop.
   - Expected:
     - You hear any configured audio feedback as before.
     - The CLI logs the transcription text.
     - The text appears at the caret position in the active window (typed in), **without requiring you to press Ctrl+V**.

2. **Clipboard behavior & clearing**
   - Immediately after a successful injection, press `Ctrl+V` in a different application to confirm the text is on the clipboard.
   - Wait for at least `clipboard_clear_delay` (default 0.75s) and then press `Ctrl+V` again to ensure clipboard clearing still works if enabled.

3. **Regression safety**
   - Toggle recording multiple times in a row to ensure repeated injections work.
   - Optionally change `primary_shortcut` in `config.json` and confirm behavior is unchanged.

---

## Next steps

If you’re happy with this plan, I will:
1. Implement the `KeyboardShortcutManager.write` helper and the Windows-aware branch in `TextInjector.inject` exactly as described above.
2. Run the basic validators (`compileall`, CLI smoke check) in this repo.
3. Summarize the concrete changes and how you can tweak behavior if needed.

Please confirm if you’d like me to proceed with this implementation, or if you’d prefer an alternative (e.g., sticking strictly to `Ctrl+V`-based pasting and instead improving logging or providing a config flag to switch to type-based injection).