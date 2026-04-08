---
name: start-ticket
description: "Ticket kickoff only (setup + plan + draft PR + failing tests). Use /dev for the full autonomous pipeline. Accepts goal or Trello card. Example: /start-ticket implement rate limiting"
user_invocable: true
---

# Start Ticket

Kicks off a new piece of work — from raw goal to failing tests that define "done." Use this when you want to set up and plan but implement manually. For full automation, use `/dev` instead.

## Commit Discipline

**Commit early and often. Push after every commit.** Don't accumulate local commits.

## Input

The user provides one of:
- **A goal string**: `/start-ticket implement rate limiting for the admin API`
- **A Trello card**: `/start-ticket https://trello.com/c/abc123`

If no argument, ask: "What are you working on? (paste a goal or Trello card URL)"

## Phase 1: Environment

### 1. Verify Worktree

Run `pwd`. Must contain `.claude/worktrees/`.

If not: STOP. Say: "Not in a worktree. Run `claude --worktree` first, then `/start-ticket` again."

### 2. Set Up .env

If `.env` doesn't exist:
- Try `cp ../../.env .env` (from main project dir)
- Fallback: `cp .env.example .env`
- Warn about API keys if copied from example

### 3. Resolve the Goal

**Trello card** (URL contains `trello.com/c/` or input starts with `trello:`):
- Parse card ID, fetch with `~/bin/trello card <ID>`
- Extract title + description as the goal
- Move to In Progress: `~/bin/trello move <ID> <IN_PROGRESS_LIST_ID>` (look up list ID via `~/bin/trello lists <BOARD_ID>` if needed)
- Note the card ID in OBJECTIVE.md for `/finish-ticket`

**Plain text**: use as-is.

## Phase 2: Understand and Plan

### 4. Research the Problem

Before planning, understand the relevant code:
- Read the project's ARCHITECTURE.md if it exists
- Search the codebase for modules/files related to the goal
- Read existing tests in the area to understand conventions and coverage
- Check `dev/context/` files for relevant learnings, decisions, gotchas

### 5. Write dev/OBJECTIVE.md

```markdown
# Objective

<One-sentence goal>

## Description

<2-3 sentences of context, informed by codebase research>

## Approach

<Bulleted plan — which files to modify, what the change looks like>

## Acceptance Criteria

- [ ] Failing unit tests written and verified failing
- [ ] Implementation makes all tests pass
- [ ] dev_checks passes
- [ ] <domain-specific criteria from the goal>

## Tracking

- Trello: <card URL or "none">
- Branch: <branch name>
- PR: <filled after creation>
```

### 6. Confirm Plan with User

Present the approach and ask: "Does this plan look right?"

Wait for confirmation before proceeding.

## Phase 3: Draft PR (early)

### 7. Create Draft PR

Get the draft PR up before writing any tests or code:

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

## Phase 4: Test-First

### 8. Write Failing Tests

Write unit tests that define the expected behavior:
- Follow the project's test conventions
- Cover the happy path, edge cases, and error conditions
- Place tests in the appropriate directory mirroring the source structure

### 9. Verify Tests Fail Correctly

Run the new tests: `uv run pytest <test_file> -v`

Confirm they fail because the feature doesn't exist, not due to infrastructure issues.

### 10. Commit and Push Tests

```bash
git add <test_files>
git commit -m "test: add failing tests for <feature>"
git push
```

### 11. Report

```
Ready to implement:
  Worktree:      <path>
  Branch:        <branch>
  PR (draft):    <URL>
  Trello:        <card URL — moved to In Progress / not linked>
  Failing tests: <N tests in M files>

The tests define what "done" looks like. Implement until they pass.
```
