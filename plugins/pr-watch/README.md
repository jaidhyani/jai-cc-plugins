# pr-watch

Watch the current branch's PR and respond to CI failures, reviews, and merge conflicts.

`/pr-watch` starts a background poll loop on the current branch's open PR. When something changes, it wakes up and acts:

- **CI failures** — fetches logs, diagnoses, fixes, pushes
- **Review comments** — addresses substantive feedback, escalates questions to the user
- **Merge conflicts** — fetches base branch, resolves, pushes
- **Approval + green checks** — notifies the user it's ready to merge

Never merges autonomously — the human always merges.

## Install

```
/install-plugin jaidhyani/jai-cc-plugins pr-watch
```
