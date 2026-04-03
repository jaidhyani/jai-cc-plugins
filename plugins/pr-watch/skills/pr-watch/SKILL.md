---
name: pr-watch
description: "This skill should be used when the user asks to \"watch PRs\", \"monitor PRs\", \"track PR changes\", \"watch for reviews\", \"babysit this PR\", \"keep an eye on CI\", \"monitor open pull requests\", or wants autonomous PR monitoring that detects and responds to CI failures, review comments, and merge conflicts."
---

# PR Watch

Monitor open GitHub PRs by blocking until a state change is detected, then respond autonomously to CI failures, review comments, and merge conflicts. Consumes zero LLM tokens while waiting.

## Two Modes

1. **Watch all** (default): monitor all open PRs for the current user, report changes
2. **Watch + respond** (`--respond`): monitor a single PR and autonomously fix CI failures, address review comments, and resolve merge conflicts

## Core Script

`${CLAUDE_PLUGIN_ROOT}/scripts/pr-watch.sh` accepts:
- `--author AUTHOR` — GitHub author filter (default `@me`)
- `--interval SECONDS` — polling interval (default `60`)

## Watch All PRs (Detection Only)

### 1. Get Baseline

```bash
gh pr list --author "@me" --state open \
  --json number,title,mergeable,commits,updatedAt \
  --jq '[.[] | {number, title, mergeable, commits: (.commits | length), updatedAt}] | sort_by(.number)'
```

Report baseline state to user.

### 2. Start Blocking Watcher

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/pr-watch.sh
```

Blocks until a change is detected.

### 3. Interpret Changes

Compare BEFORE/AFTER JSON:
- **New commits**: commit count increased
- **Merge status changes**: MERGEABLE to CONFLICTING or vice versa
- **PRs disappeared**: verify with `gh pr view NUMBER --json state,mergedAt`
- **New PRs**: numbers in AFTER not in BEFORE
- **updatedAt-only**: check `gh pr view NUMBER --json comments --jq '.comments[-1]'`

### 4. Re-launch

After reporting, restart the watcher to continue monitoring.

## Watch + Respond (Single PR)

For autonomous monitoring of a single PR with active response to issues. Identify the target PR from user input (number, URL, or current branch).

### 1. Capture Baseline

```bash
PR=$(gh pr view --json number --jq .number)
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
PREV_COMMENTS=$(gh pr view $PR --json comments --jq '.comments | length')
PREV_REVIEWS=$(gh pr view $PR --json reviews --jq '.reviews | length')
```

Report: "Watching PR #N — polling every 90s for CI, reviews, comments, and conflicts."

### 2. Launch Background Monitor

Start a background poll loop (`run_in_background: true` Bash command):

```bash
PR=<number>
PREV_COMMENTS=<baseline>
PREV_REVIEWS=<baseline>
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
        echo "ALERT:NEW_COMMENTS count=$NEW_COMMENTS prev=$PREV_COMMENTS"
        exit 0
    fi

    NEW_REVIEWS=$(gh pr view $PR --json reviews --jq '.reviews | length')
    if [ "$NEW_REVIEWS" -gt "$PREV_REVIEWS" ]; then
        echo "ALERT:NEW_REVIEW"
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

    DECISION=$(gh pr view $PR --json reviewDecision --jq '.reviewDecision')
    ALL_PASS=$(gh pr checks $PR --json state --jq '.[].state' 2>/dev/null | sort -u)
    if [ "$DECISION" = "APPROVED" ] && ! echo "$ALL_PASS" | grep -qE "FAILURE|PENDING"; then
        echo "INFO:READY_TO_MERGE"
        exit 0
    fi
done
echo "INFO:TIMEOUT"
```

### 3. Handle Alerts

When the monitor exits, act on the signal, then restart from step 2 with updated baselines.

#### ALERT:CI_FAILURE

1. Identify failed runs: `gh pr checks $PR`
2. Fetch logs: `gh run view <run_id> --log-failed`
3. Diagnose — read relevant source files
4. Fix, run tests locally, commit and push
5. Restart monitor

#### ALERT:NEW_COMMENTS

1. Fetch new comments:
   ```bash
   gh pr view $PR --json comments --jq '.comments | .[-<delta>:] | .[] | "@\(.author.login): \(.body[0:500])"'
   ```
2. Fetch inline review comments:
   ```bash
   gh api repos/$REPO/pulls/$PR/comments --jq '.[] | "\(.path):\(.line // .original_line) — \(.user.login): \(.body)"'
   ```
3. Address each (see "Addressing Feedback")
4. Restart monitor

#### ALERT:NEW_REVIEW

1. Fetch review:
   ```bash
   gh pr view $PR --json reviews --jq '.reviews[-1] | "@\(.author.login) (\(.state)): \(.body)"'
   ```
2. APPROVED — report to user, check if all checks pass
3. CHANGES_REQUESTED / COMMENTED — fetch inline comments and address
4. Restart monitor

#### ALERT:MERGE_CONFLICT

1. Merge base branch:
   ```bash
   BASE=$(gh pr view $PR --json baseRefName --jq '.baseRefName')
   git fetch origin $BASE && git merge origin/$BASE
   ```
2. Resolve conflicts, run tests, commit and push
3. Restart monitor

#### INFO:PR_MERGED / INFO:PR_CLOSED

Report status. Stop monitoring.

#### INFO:READY_TO_MERGE

Report: "PR #N is approved and all checks pass. Ready to merge."
Continue monitoring — never merge autonomously.

#### INFO:TIMEOUT

Report timeout (~2 hours). Suggest re-running to restart.

### 4. Addressing Feedback

For each comment:
- **CI failures**: diagnose from logs, fix, test locally, commit and push
- **Substantive code feedback**: make the change, test, commit and push each fix separately
- **Questions or style preferences**: ask the user — do not guess
- **Acknowledged nitpicks**: reply on the PR thread

After all items:
1. Run the project's test suite
2. Run dev_checks if available: `"$(git rev-parse --show-toplevel)/scripts/dev_checks.sh"`
3. Formatting fixes from dev_checks get their own commit

### 5. Commit Discipline

Commit and push after every logical fix. Never batch unrelated fixes. Formatting/lint fixes from dev_checks get their own commit.

## Team Context

When operating as a teammate, use `SendMessage` to notify the lead of changes:
- "PR #194: new commit pushed (11 -> 12)"
- "PR #187: MERGED at 00:36 UTC"
- "PR #184: now CONFLICTING (was MERGEABLE)"
- "PR #152: CI failed — fixing flaky test in auth_test.go"
