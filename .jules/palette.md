# Palette's Journal

## 2024-05-22 - Visual Feedback Discrepancy
**Learning:** The memory/documentation claimed a persistent visual status indicator existed, but the code revealed only log messages were used. Visual feedback (spinners) provides immediate mode assurance that logs (historical) cannot.
**Action:** Always verify "known" features in code before assuming they exist. When implementing CLI tools, prioritize persistent state indicators over scrolling logs for the primary interaction loop.
