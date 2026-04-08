---
name: finish-ticket
description: "Wrap up after implementation: cleanup, dev_checks, e2e, changelog, PR ready, monitor feedback, wait for merge. Use when joining mid-flow after implementation. /dev does this automatically."
user_invocable: true
---

# Finish Ticket

Takes over from "implementation complete" and drives through to merge. The human makes the merge decision. Once merged, closes out tracking. Use this when joining a session mid-flow. `/dev` runs this automatically as part of the full pipeline.

## Commit Discipline

**Commit early and often. Push after every commit.**

- When dev_checks or formatting fixes something, commit and push immediately (`style: fix lint/formatting`)
- After cleanup, commit and push before moving on
- After addressing review comments, commit and push each logical fix separately
- Never accumulate local commits

## Phase 1: Validate

### 1. Verify Worktree

Run `pwd`. Must contain `.claude/worktrees/`.

If not: STOP with error.

### 2. Read Context

- Read `dev/OBJECTIVE.md` for the goal, tracking info, and Trello reference
- Note the Trello card ID if present (for close-out)

### 3. Verify Tests Pass

Run unit tests: `uv run pytest tests/unit_tests/ -v`

If tests fail: fix them. Do not proceed until unit tests pass. **Commit and push** any fixes.

### 4. Run Cleanup

Invoke the `/cleanup` skill to fix code quality issues. Wait for completion.

**Commit and push** cleanup fixes immediately (`style: cleanup pass`).

### 5. Run Dev Checks

Execute `"$(git rev-parse --show-toplevel)/scripts/dev_checks.sh"`.

- **Passes**: if there are staged changes from auto-formatting, **commit and push** (`style: fix lint/formatting`), then proceed.
- **Test failures**: investigate, fix, **commit and push**, re-run.

### 6. E2E Tests

Check if the changes warrant e2e tests.

If appropriate:
- Check `docker compose ps` — offer `"$(git rev-parse --show-toplevel)/scripts/quick_start.sh"` if not running
- Run targeted e2e tests first, broader suite if they pass
- Fix failures, **commit and push** fixes

If changes are purely internal with no API surface change, skip with a note.

## Phase 2: Ship

### 7. Add Changelog Fragment

If a changelog fragment doesn't already exist for this branch:

1. Infer category from commit prefixes (`feat`→Features, `fix`→Fixes, `refactor`→Refactors, else→Chores & Docs)
2. Get PR number: `gh pr view --json number --jq .number`
3. Write `changelog.d/<branch-name>.md` with frontmatter (see `changelog.d/README.md`)
4. Commit and push.

### 8. Clear Dev Files

- Empty `dev/OBJECTIVE.md`
- Empty `dev/NOTES.md`

### 9. Final Commit, Push, and Promote PR

```bash
git add -A
git commit -m "chore: <objective-handle> is ready"
git push
gh pr ready
```

## Phase 3: Review Loop

This phase loops until the PR is approved and all checks pass.

### 10. Check for Feedback

```bash
gh pr checks <number>
gh pr view <number> --json reviews,comments,state,reviewDecision
```

### 11. Address CI Failures

If checks failed:
- Fetch logs: `gh run view <run_id> --log-failed`
- Fix, run dev_checks, **commit and push** the fix

### 12. Address Review Comments

Fetch comments:
```bash
gh pr view <number> --json reviews --jq '.reviews[] | select(.state != "APPROVED") | "\(.author.login) (\(.state)): \(.body)"'
gh api repos/<owner>/<repo>/pulls/<number>/comments --jq '.[] | "\(.path):\(.line // .original_line) — \(.user.login): \(.body)"'
```

For each comment:
- Substantive feedback: make changes, run tests
- Questions or style preferences: ask the user how to respond
- Run dev_checks — **commit and push** any formatting fixes separately
- **Commit and push** review response (`fix: address review — <summary>`)

### 13. Check Approval Status

**If approved and checks pass**: tell the user the PR is ready to merge. **Do NOT merge.**

**If changes requested or checks failing**: loop back to step 11.

**If waiting for review**: tell the user and ask if they want to wait or come back later.

### 14. Start Background Monitor

After promoting the PR (Step 9) or after addressing feedback, launch the background PR monitor (same pattern as `/pr` Step 6). This monitors CI, comments, reviews, and merge conflicts every 90 seconds and alerts when action is needed.

When an alert fires, loop back to Step 11 (CI failures) or Step 12 (comments/reviews) as appropriate.

## Phase 4: Close Out (after human merges)

### 15. Wait for Merge

Monitor PR state. When `MERGED`:

If a Trello card was linked:
- Move to Done: `~/bin/trello move <CARD_ID> <DONE_LIST_ID>`
- Comment: "Merged in PR #<number>"

```
Ticket complete:
  PR:        <URL> (merged)
  CHANGELOG: <entry>
  Trello:    <moved to Done / not linked>

Done.
```
