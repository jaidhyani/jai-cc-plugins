---
name: address-pr
description: "Mid-review entry point: fetch PR comments and CI failures, address them, validate, push. Use when jumping into an existing PR. /dev handles this automatically."
user_invocable: true
---

# Address PR Feedback

For when you jump into a session with an existing PR that needs attention. Fetches comments and CI failures, addresses them, validates, and pushes. `/dev` does this automatically in its review loop.

## Commit Discipline

**Commit and push after every logical fix.** Don't batch all review fixes into one commit. Formatting/lint fixes from dev_checks get their own commit.

## Workflow

### 1. Verify Worktree

Run `pwd`. Must contain `.claude/worktrees/`.

If not: STOP with error.

### 2. Identify the PR

```bash
gh pr view --json number,url,title
```

If no PR exists for this branch, tell the user and stop.

### 3. Gather All Feedback

**Review comments:**
```bash
gh repo view --json nameWithOwner --jq .nameWithOwner
gh pr view <number> --json reviews --jq '.reviews[] | select(.state != "APPROVED") | "\(.author.login) (\(.state)): \(.body)"'
gh api repos/<owner>/<repo>/pulls/<number>/comments --jq '.[] | "\(.path):\(.line // .original_line) — \(.user.login): \(.body)"'
```

**CI status:**
```bash
gh pr checks <number>
```

If checks failed, fetch logs:
```bash
gh run view <run_id> --log-failed
```

Present everything clearly — comments and failures together.

### 4. Address Feedback

Work through each item:
- **CI failures**: diagnose, fix, run tests locally to confirm, **commit and push** the fix
- **Code review — substantive**: make changes, run tests, **commit and push** each logical fix separately
- **Code review — questions/style**: ask the user how to respond

### 5. Validate

Run full local validation:
1. Unit tests: `uv run pytest tests/unit_tests/ -v`
2. Dev checks: `"$(git rev-parse --show-toplevel)/scripts/dev_checks.sh"`

If dev_checks fixes formatting/lint, **commit and push** those separately (`style: fix lint/formatting`).

### 6. Final Check

Run `git status` to verify nothing is uncommitted. Everything should already be pushed from step 4.

### 7. Report

```bash
gh pr view <number> --json reviewDecision,mergeStateStatus
```

Report:
- What changed (list of commits pushed)
- Which comments were addressed
- Whether the PR is now approved / ready to merge
- Any items still needing user input

The human decides when to merge.
