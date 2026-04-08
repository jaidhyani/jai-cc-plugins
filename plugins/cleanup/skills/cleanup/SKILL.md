---
name: cleanup
description: This skill should be used when the user asks to "clean up the code", "cleanup", "do a cleanup pass", "review and fix code quality", "scan and fix tech debt", "simplify and refactor", "simplify recent changes", "code quality sweep", "tidy up", "refactor this", "refactor pass", "simplification pass", "dead code removal", "reduce complexity", "code review pass", or wants a combined scan-fix-verify workflow that finds issues, fixes safe ones, and reports the rest.
---

# Cleanup

A single-pass workflow that scans for code quality issues, fixes what can be safely fixed, and reports what needs human decision. Combines discovery, refactoring, and verification into one sweep.

## Scope

Default to the narrowest relevant scope. Escalate only when the user asks for broader coverage.

1. **PR/branch scope** (default): If on a feature branch, scope to changes vs the base branch (`git diff main...HEAD` + uncommitted work)
2. **Recent changes**: If on main with uncommitted work or recent commits, scope to those changes
3. **Specified target**: If the user names a directory, file, or module, scope to that
4. **Broader sweep**: Only scan the full project when explicitly requested ("scan the whole codebase", "project-wide cleanup")

## Phase 1: Scan

Run these scans in parallel across the scoped files:

**Dead code** — Unused imports, functions with no callers, unreachable branches, commented-out code blocks, unused variables/parameters.

**Logic complexity** — Functions over 50 lines, nesting deeper than 3 levels, complex conditionals that should be extracted into named variables, chains of nested ifs that should be early returns.

**Duplication** — Identical or near-identical multi-line blocks appearing 3+ times.

**Debt markers** — TODO, FIXME, HACK, XXX comments.

**Excessive parameters** — Functions with more than 5 parameters, parameters always passed the same value, parameters derivable from other parameters.

**Premature optimization** — Clever-but-obscure code with straightforward alternatives, caching or batching that adds complexity without measured benefit.

## Phase 2: Fix

Apply fixes for issues that are **safe to change** — meaning behavior is preserved and the change is unambiguous:

- Remove dead code (unused imports, unreachable branches, unused functions)
- Convert nested ifs to early returns
- Extract complex conditionals into named intermediate variables
- Flatten unnecessary nesting
- Remove parameters that are unused or always the same value
- Replace obscure code with straightforward alternatives
- Remove commented-out code blocks

**Do not fix** without explicit approval:
- Duplicated patterns (extracting shared code changes interfaces)
- Renaming for clarity (subjective)
- Anything that changes public API surface
- TODOs/FIXMEs (they represent intentional deferred work)

## Phase 3: Verify

Run the project's build and test suite. All existing tests must pass. If a test fails, revert that specific fix and re-run the test suite to confirm the remaining fixes are clean. A cleanup pass must never introduce regressions.

## Phase 4: Report

After fixes are applied and verified, output a short report of **remaining items** that need human decision:

```markdown
## Cleanup Report

### Fixed
- Brief list of what was changed

### Remaining (needs decision)

#### Duplication
- files: description of pattern

#### Debt Markers
- file:line: comment text

#### Rename Opportunities
- file:symbol: suggested rename

#### Other
- file: description
```

Keep the report concise. Omit empty sections.
