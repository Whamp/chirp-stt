## 2024-05-24 - Path Traversal in ConfigManager
**Vulnerability:** The `model_dir` method in `ConfigManager` sanitized `model_name` using `re.sub` but allowed `.` and did not collapse `..`. This allowed `model_name=".."` to resolve to the parent directory of `models_root`.
**Learning:** Even when using allowlists (regex), check for sequences that have special meaning in file paths (like `..`). Simply stripping invalid characters isn't enough if the remaining characters can form a traversal payload.
**Prevention:** Collapse multiple dots (`..` -> `.`) or explicitly check that the resolved path is within the intended root directory (`path.resolve().is_relative_to(root)`).
