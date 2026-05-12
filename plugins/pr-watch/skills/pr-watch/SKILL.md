---
name: pr-watch
description: "This skill should be used when the user asks to \"watch this PR\", \"monitor the PR\", \"keep an eye on CI\", \"watch for reviews\", \"babysit this PR\", or wants autonomous PR monitoring that detects and responds to CI failures, review comments, and merge conflicts on the current branch's PR."
---

# PR Watch

Monitor the current branch's PR autonomously — detect and respond to CI failures, review comments, and merge conflicts. Consumes zero LLM tokens while waiting.

## Assumptions

- The current branch has an open PR. If not, stop with: "No open PR on this branch."
- The working directory is the repo being monitored.

## Commit Discipline

Commit and push after every logical fix. Never batch unrelated fixes. Formatting/lint fixes from dev_checks get their own commit.

## Workflow

### 1. Capture Baseline

```bash
PR=$(gh pr view --json number --jq .number)
REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
PREV_COMMENTS=$(gh pr view $PR --json comments --jq '.comments | length')
PREV_REVIEWS=$(gh pr view $PR --json reviews --jq '.reviews | length')
```

Confirm the PR is open. If merged or closed, report status and stop.

Report: "Watching PR #N — polling every 60s for CI, reviews, comments, and conflicts."

### 2. Launch Background Monitor

Start a background poll loop (`run_in_background: true` Bash command):

```bash
PR=<number>
PREV_COMMENTS=<baseline>
PREV_REVIEWS=<baseline>
ITER=0; MAX_ITER=120

while [ "$ITER" -lt "$MAX_ITER" ]; do
    sleep 60
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

Report timeout (~2 hours). Suggest re-running `/pr-watch` to restart.

## Future: Webhook Mode

Polling is a stopgap. The long-term plan is ephemeral Cloudflare Worker webhooks — spin up a temporary endpoint, register it with GitHub, relay events to the local session, tear it down when the PR closes. When that infra exists, replace the poll loop with it.

### 4. Addressing Feedback

#### Triage Before Acting

For each concern, classify first, act second:

- **Real defect / real polish** → fix, commit, push.
- **Reviewer hypothetical** ("what if Anthropic adds a field", "what if the transform raises") → push back in one sentence. The code does what it does; a doc note explaining that adds nothing for the next reader.
- **Bikeshed** → skip with a one-line acknowledgement.
- **Real question / style preference** → ask the user, don't guess.

**The trap is "add a doc/comment explaining current behavior" as a response to a hypothetical.** Each note is individually cheap; cumulatively they bury the design under defensive scaffolding. Module docstrings that started at 13 lines balloon to 30+ over 5–7 review rounds. Bar for adding a comment in response to review: would a fresh reader of the file (not the reviewer who's already running thought experiments) be confused without it? If no, push back.

**Push back is brief.** One sentence per concern. "Skipping — `AnthropicToolUseBlock` is a closed TypedDict." "Standard Python exception propagation; pipeline already handles it." "Already addressed (commit X)." Don't argue, just classify and move on.

**Watch for accretion across rounds.** Before round 3, re-read the touched files cold. Anything that would feel like noise to a fresh reader gets cut now, regardless of which round added it.

#### Per Item

- **CI failures**: diagnose from logs, fix, test locally, commit and push
- **Substantive code feedback**: each fix gets its own commit
- **Acknowledged nitpicks**: brief PR reply, no code change

After all items:
1. Run the project's test suite
2. Run dev_checks if available: `"$(git rev-parse --show-toplevel)/scripts/dev_checks.sh"`
3. Formatting fixes from dev_checks get their own commit

## Team Context

When operating as a teammate, use `SendMessage` to notify the lead of changes:
- "PR #194: CI failed — fixing flaky test in auth_test.go"
- "PR #184: now CONFLICTING — resolving merge conflict"
- "PR #187: approved, all checks green — ready to merge"
