---
name: dev
description: "End-to-end autonomous development: goal → plan → TDD → implement → validate → PR → address feedback → wait for merge → close tracking. Human approves plan and merge only. Example: /dev implement rate limiting"
user_invocable: true
---

# /dev — Full Autonomous Development Pipeline

One skill to go from goal to merged PR. The human intervenes at two gates:
1. **Plan approval** — before implementation begins
2. **Merge** — the human clicks merge when ready

Everything else runs autonomously: test writing, implementation, validation, PR creation, CI monitoring, addressing review comments.

## Commit Discipline

**Commit early and often. Push after every commit.**

- Commit after every meaningful unit of progress (a test written, a function implemented, a bug fixed)
- Always push immediately after committing — don't accumulate local commits
- When dev_checks or formatting fixes something, commit and push those fixes immediately as their own commit (e.g., `style: fix lint/formatting`)
- After cleanup, commit and push before moving on
- After addressing review comments, commit and push each logical fix separately
- Small, frequent commits are always better than large, infrequent ones

## What NOT to Include in PRs

- **Design docs / spec files** — these are working artifacts for the brainstorming/planning phase, not deliverables. Do not commit them to the repo or include them in PRs.

## Input

- **A goal string**: `/dev implement rate limiting for the admin API`
- **A Trello card**: `/dev https://trello.com/c/abc123`

If no argument, ask: "What should I build? (goal or Trello card URL)"

---

## Stage 1: Setup

### 1.1 Verify Worktree

Run `pwd`. Must contain `.claude/worktrees/`.

If not: STOP. "Not in a worktree. Run `claude --worktree` first, then `/dev` again."

### 1.2 Set Up .env

If `.env` doesn't exist:
- Try `cp ../../.env .env`
- Fallback: `cp .env.example .env`
- Warn if copied from example

### 1.3 Resolve Goal

**Trello card** (URL contains `trello.com/c/`):
- Fetch card: `~/bin/trello card <ID>`
- Extract title + description as goal
- Move to In Progress: `~/bin/trello move <ID> <LIST_ID>` (look up via `~/bin/trello lists <BOARD_ID>`)
- Save card ID for later

**Plain text**: use as-is.

---

## Stage 2: Plan (HUMAN GATE)

### 2.1 Research

- Read ARCHITECTURE.md if it exists
- Search codebase for relevant modules
- Read existing tests in the area
- Check `dev/context/` for learnings, decisions, gotchas

### 2.2 Write Plan

Write `dev/OBJECTIVE.md`:

```markdown
# Objective

<One-sentence goal>

## Description

<Context informed by codebase research>

## Approach

- <Step 1: what to change and why>
- <Step 2: ...>
- <Step 3: ...>

## Test Strategy

- Unit tests: <what to test, which files>
- E2E tests: <whether needed, which scenarios>

## Acceptance Criteria

- [ ] Failing unit tests written
- [ ] Implementation makes all tests pass
- [ ] dev_checks passes
- [ ] <domain-specific criteria>

## Tracking

- Trello: <card URL or "none">
- Branch: <branch>
- PR: <filled later>
```

### 2.3 Get Plan Approval

Present the plan to the user. **STOP and wait for approval.**

Do not proceed until the user confirms. Adjust the plan if they have feedback.

---

## Stage 3: Draft PR + Test-First

### 3.1 Create Draft PR Early

Commit the objective and push immediately — get the draft PR up before writing any code:

```bash
git add dev/OBJECTIVE.md
git commit -m "chore: set objective to <short-handle>"
git push -u origin $(git rev-parse --abbrev-ref HEAD)
gh pr create --draft --title "<type>: <title>" --body "$(cat <<'EOF'
## Objective

<objective statement>

## Approach

<approach from OBJECTIVE.md>

## Acceptance Criteria

<criteria>
EOF
)"
```

Update `dev/OBJECTIVE.md` Tracking section with the PR URL. If Trello card is linked, comment the PR URL on the card.

### 3.2 Write Failing Tests

Write unit tests that define the expected behavior:
- Follow existing test patterns in the project
- Cover happy path, edge cases, error conditions
- Place in the right directory mirroring source structure

### 3.3 Verify Tests Fail Correctly

Run: `uv run pytest <test_files> -v`

Confirm tests fail because the feature doesn't exist, not due to import errors or test bugs. Fix test infrastructure issues until they fail cleanly.

### 3.4 Commit and Push Tests

```bash
git add <test_files>
git commit -m "test: add failing tests for <feature>"
git push
```

---

## Stage 4: Implement

### 4.1 Build It

Implement the feature/fix according to the plan.

**Use tests as the feedback loop**: after each significant change, run the relevant tests to check progress. Don't wait until "done" to test — test continuously.

```bash
uv run pytest <test_files> -v
```

**Commit at each milestone**: when a test starts passing, when a module is complete, when a logical chunk of work is done. Push every commit.

### 4.2 All Tests Pass

Keep iterating until all new tests pass AND existing tests still pass:

```bash
uv run pytest tests/unit_tests/ -v
```

Commit and push when all tests are green.

---

## Stage 5: Validate

### 5.1 Run Cleanup

Invoke `/cleanup` on the changed files to scan for dead code, complexity, duplication, and other quality issues. Fix safe issues, report the rest.

**Commit and push any fixes immediately** (e.g., `style: cleanup pass`).

### 5.2 Code Review

Invoke the `superpowers:requesting-code-review` skill to self-review the implementation against the plan and acceptance criteria. Address any issues found before proceeding.

### 5.3 Run Dev Checks

Execute the project's QC suite — `"$(git rev-parse --show-toplevel)/scripts/dev_checks.sh"` or equivalent (formatting, linting, type checking, tests, coverage). Check the project's CLAUDE.md or build docs for the right command if `dev_checks.sh` doesn't exist.

The script auto-stages formatting fixes. After it passes:
- If there are staged changes: **commit and push** (`style: fix lint/formatting`)
- Test failures: investigate, fix, **commit and push**, re-run

### 5.4 Smoke Test

**Always do a basic smoke test** of the actual user workflow, even when the test strategy says no formal e2e tests are needed. Unit tests verify logic; smoke tests verify the feature actually works end-to-end. Run the feature the way a user would and confirm it doesn't crash.

This step catches integration issues that unit tests miss (e.g., import-time side effects, config loading order, missing files).

### 5.5 E2E Tests

**Before building any manual test setup**, search for existing test infrastructure:

1. Check `tests/` for existing e2e fixtures and test files that cover the scenario
2. Read any `CLAUDE.md` in the test directories — they document available test tiers and helpers
3. Run existing e2e/integration tests that cover the changed code paths first
4. Only build a manual setup if no existing infrastructure covers the scenario

If the test strategy calls for formal e2e tests:
- Run existing e2e suites that cover the scenario first (in-process, mock, or real backend)
- Fix failures, **commit and push** fixes
- For manual validation beyond existing tests: use existing test helpers (fixtures, scripts) rather than ad-hoc process management

---

## Stage 6: Ship

### 6.1 Add Changelog Fragment

Add a changelog fragment. If one doesn't already exist for this branch:

1. Infer category from commit prefixes (`feat`→Features, `fix`→Fixes, `refactor`→Refactors, else→Chores & Docs)
2. Get PR number: `gh pr view --json number --jq .number`
3. Write `changelog.d/<branch-name>.md`:

```markdown
---
category: <CATEGORY>
pr: <PR_NUMBER>
---

**<Title>**: <summary from commits>
```

4. Commit and push.

### 6.2 Clear Dev Files

- Empty `dev/OBJECTIVE.md`
- Empty `dev/NOTES.md`

### 6.3 Final Commit and Promote PR

```bash
git add -A
git commit -m "chore: <objective-handle> is ready"
git push
gh pr ready
```

---

## Stage 7: Monitor and React

This stage runs autonomously until the PR is merged.

### 7.1 Set Up Background Monitor

After pushing, launch a background monitor (`run_in_background: true` Bash command) that polls for CI failures, new comments, reviews, and merge conflicts:

```bash
PR=$(gh pr view --json number --jq .number)
PREV_COMMENTS=$(gh pr view $PR --json comments --jq '.comments | length')
PREV_REVIEWS=$(gh pr view $PR --json reviews --jq '.reviews | length')
ITER=0; MAX_ITER=80

while [ "$ITER" -lt "$MAX_ITER" ]; do
    sleep 90
    ITER=$((ITER + 1))

    CI=$(gh pr checks $PR --json state --jq '.[].state' 2>/dev/null | sort -u)
    if echo "$CI" | grep -q "FAILURE"; then
        echo "ALERT:CI_FAILURE"
        gh pr checks $PR
        exit 0
    fi

    NEW_COMMENTS=$(gh pr view $PR --json comments --jq '.comments | length')
    if [ "$NEW_COMMENTS" -gt "$PREV_COMMENTS" ]; then
        echo "ALERT:NEW_COMMENTS"
        gh pr view $PR --json comments --jq '.comments[-1] | "@\(.author.login): \(.body[0:500])"'
        exit 0
    fi

    NEW_REVIEWS=$(gh pr view $PR --json reviews --jq '.reviews | length')
    if [ "$NEW_REVIEWS" -gt "$PREV_REVIEWS" ]; then
        echo "ALERT:NEW_REVIEW"
        gh pr view $PR --json reviews --jq '.reviews[-1] | "@\(.author.login) (\(.state)): \(.body[0:500])"'
        exit 0
    fi

    MERGEABLE=$(gh pr view $PR --json mergeable --jq '.mergeable')
    if [ "$MERGEABLE" = "CONFLICTING" ]; then
        echo "ALERT:MERGE_CONFLICT"
        exit 0
    fi

    STATE=$(gh pr view $PR --json state --jq '.state')
    if [ "$STATE" = "MERGED" ] || [ "$STATE" = "CLOSED" ]; then
        echo "INFO:PR_$STATE"
        exit 0
    fi
done
echo "INFO:TIMEOUT"
```

When the monitor exits, act on the alert:
- **ALERT:CI_FAILURE** — fetch logs with `gh run view <run_id> --log-failed`, diagnose, fix, push
- **ALERT:NEW_COMMENTS / ALERT:NEW_REVIEW** — fetch full comment, address substantive feedback, push
- **ALERT:MERGE_CONFLICT** — `git fetch origin main && git merge origin/main`, resolve, push
- **INFO:PR_MERGED** — report success
- **INFO:TIMEOUT** — tell user the monitor timed out after ~2 hours, ask if they want to restart

When notified, handle whichever condition triggered:

### 7.2 Handle CI Failures

If checks fail:
- Fetch logs: `gh run view <run_id> --log-failed`
- Diagnose and fix
- Run dev_checks locally
- **Commit and push** the fix
- Return to 7.1

### 7.3 Handle Merge Conflicts

If `mergeable` is `CONFLICTING`:
- `git fetch origin main && git merge origin/main`
- Resolve conflicts, **commit and push**
- Return to 7.1

### 7.4 Address Review Comments

Fetch and present all comments:
```bash
gh pr view <number> --json reviews --jq '.reviews[] | select(.state != "APPROVED") | "\(.author.login) (\(.state)): \(.body)"'
gh api repos/<owner>/<repo>/pulls/<number>/comments --jq '.[] | "\(.path):\(.line // .original_line) — \(.user.login): \(.body)"'
```

For each comment:
- **Substantive code feedback**: make changes, run tests to validate
- **Questions or style preferences**: ask the user how to respond

After addressing comments:
- Run unit tests
- Run dev_checks — if it fixes anything, **commit and push the fix separately**
- **Commit and push** the review response (e.g., `fix: address review — <summary>`)
- Return to 7.1

### 7.5 Notify When Ready to Merge

When `reviewDecision` is `APPROVED` and all checks pass:

Tell the user: "PR is approved and all checks pass. Ready to merge when you are."

**Do NOT merge.** The human merges.

### 7.6 Wait for Merge

Monitor PR state:
```bash
gh pr view <number> --json state --jq .state
```

When state is `MERGED`, proceed to Stage 8.

---

## Stage 8: Close Out

### 8.1 Update Trello

If a Trello card was linked:
- Move to Done: `~/bin/trello move <CARD_ID> <DONE_LIST_ID>`
- Comment: "Merged in PR #<number>"

### 8.2 Final Report

```
Ticket complete:
  PR:        <URL> (merged)
  CHANGELOG: <entry>
  Trello:    <moved to Done / not linked>

Done.
```
