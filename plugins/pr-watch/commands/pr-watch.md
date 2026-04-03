---
name: pr-watch
description: Monitor PRs for changes and respond to CI failures, reviews, and conflicts
---

Monitor open GitHub PRs. Two modes:

**Watch all** (no args): detect changes across all your open PRs, report what happened.
**Watch + respond** (with PR): autonomously monitor a single PR and respond to CI failures, review comments, and merge conflicts.

Use the pr-watch skill for detailed workflow guidance.

Examples:
- `/pr-watch` — watch all open PRs for changes
- `/pr-watch 123` — watch PR #123 and respond to issues
- `/pr-watch https://github.com/org/repo/pull/123` — same, with URL
