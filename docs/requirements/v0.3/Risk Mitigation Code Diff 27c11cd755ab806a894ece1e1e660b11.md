# Risk Mitigation: Code Diff

Created by: Brock Butler
Created time: September 27, 2025 10:12 PM
Last edited by: Brock Butler
Last updated time: September 27, 2025 10:13 PM
Parent item: v1 White Paper: Code Diff Storage, Rewinds, Replays, Bookmarks, and Visualization (https://www.notion.so/v1-White-Paper-Code-Diff-Storage-Rewinds-Replays-Bookmarks-and-Visualization-27b11cd755ab809ca950e00144cb5d7a?pvs=21)

**Risks & Mitigations:** 

| Risk | Mitigation |
| --- | --- |
| Batch accept hides mistakes | Always allow preview; record batch scope & rationale; post-merge preflight must pass. |
| Semantic block detection flaky | Behind feature flag; per-file batch works without it; fallback to text. |
| Binary previews limited in terminal | Provide strong metadata + OS `open`; M1 handlers for rich previews. |
| User confusion on ours/theirs | Always print banner: `OURS = <branch/bookmark + author>`, `THEIRS = <branch/bookmark + author>`. |