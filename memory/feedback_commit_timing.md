---
name: Wait for explicit commit approval
description: Never commit until the user says "ok commit now" — user explicitly requires approval before every git commit
type: feedback
---

Do NOT run `git commit` until the user explicitly says "ok commit now" (or equivalent clear approval).

**Why:** User was repeatedly interrupted by premature commits during release and README workflows. They want to review changes before committing.

**How to apply:** After staging files, stop and report what's staged. Wait for the user to say "ok commit now" before running `git commit`. This applies in all contexts — fixes, releases, docs, everything.
