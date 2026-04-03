# pr-watch

Monitor PRs and respond to CI failures, reviews, and conflicts.

## Modes

**Watch all** (`/pr-watch`): Blocks until any of your open PRs change state (new commits, merge conflicts, merges), then reports what happened. Zero token consumption while waiting.

**Watch + respond** (`/pr-watch 123`): Autonomously monitors a single PR and responds to issues:
- CI failures — fetches logs, diagnoses, fixes, pushes
- Review comments — addresses substantive feedback, asks user about style/questions
- Merge conflicts — fetches base branch and resolves
- Approval + green checks — notifies user it's ready to merge

Never merges autonomously — the human always merges.

## Install

```
/install-plugin jaidhyani/jai-cc-plugins pr-watch
```
