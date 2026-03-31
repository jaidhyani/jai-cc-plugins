# jai-cc-plugins

Claude Code plugins by jaidhyani.

## Installation

Add this marketplace:
```bash
/plugin marketplace add jaidhyani/jai-cc-plugins
```

## Available Plugins

### claude-archivist

Automatically archive Claude Code session transcripts to prevent data loss.

**Install:**
```bash
/plugin install claude-archivist@jai-cc-plugins
```

**Features:**
- Archives sessions on SessionEnd, PreCompact, and periodically during long sessions
- Incremental backup - only copies changed files
- Gzip compression
- Mirrors source directory structure to `~/.claude-archive/`
- Restore deleted sessions without overwriting existing ones

**Commands:**
- `/claude-archivist:archive` - Archive current session
- `/claude-archivist:archive-all` - Archive all sessions (full scan)
- `/claude-archivist:archive-status` - Show backup statistics
- `/claude-archivist:restore-from-archive` - Restore deleted sessions
- `/claude-archivist:configure-archive` - Configure settings

**Configuration:**

Create `~/.claude/claude-archivist.local.md`:
```yaml
---
archive_path: ~/.claude-archive
backup_interval_minutes: 30
enabled: true
---
```

### timestamp-tracker

Track timestamps of user prompts and Claude responses for temporal context.

**Install:**
```bash
/plugin install timestamp-tracker@jai-cc-plugins
```

**Features:**
- Lightweight automatic timestamp tracking via hooks (UserPromptSubmit, Stop)
- No commands needed - captures timing metadata in the background

### imagine

Generate images using Gemini 3 Pro (Nano Banana Pro).

**Install:**
```bash
/plugin install imagine@jai-cc-plugins
```

**Features:**
- Aspect ratio options: 1:1, 16:9, 9:16, 4:3, 3:4
- Size options: 1K, 2K, 4K
- Optional reference image for guided generation
- Defaults to 1:1 at 2K resolution

**Commands:**
- `/imagine` - Generate an image from a text prompt

### ultrapowers

Development discipline without ceremony. Brainstorming, debugging, TDD, verification, planning, code review, and agent coordination.

Based on the official Anthropic [superpowers](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/superpowers) plugin.

**Install:**
```bash
/plugin install ultrapowers@jai-cc-plugins
```

**Skills:**
- `/ultrapowers:brainstorm` - Design-before-code discipline, scales from quick clarification to deep collaborative design
- `/ultrapowers:debugging` - Systematic root-cause investigation
- `/ultrapowers:tdd` - Test-driven development workflow (red-green-refactor)
- `/ultrapowers:verify` - Verification before completion claims
- `/ultrapowers:plans` - Implementation plan writing and execution
- `/ultrapowers:code-review` - Technical evaluation and feedback handling
- `/ultrapowers:agents` - Parallel dispatch and sequential task orchestration

### devil

Devil's advocate agent for aggressive critique, adversarial review, and finding flaws in designs, code, and plans.

**Install:**
```bash
/plugin install devil@jai-cc-plugins
```

**Features:**
- Dedicated adversarial agent that actively investigates code, history, and builds concrete counterexamples
- Focuses on impact over correctness - one fatal flaw over twenty style complaints
- Multiple output formats: structured teardown, Socratic questioning, rapid-fire concerns, or single fatal flaw
- No softening, no solutions - attack only

**Skills:**
- `/devil` - Dispatch the devil's advocate agent against the current plan, design, or code

### pr-watch

Efficient PR monitoring that blocks until changes are detected, saving LLM tokens.

**Install:**
```bash
/plugin install pr-watch@jai-cc-plugins
```

**Features:**
- Establishes baseline snapshot of open PRs and polls for state changes
- Detects: new commits, merge status changes, PR merges, new PRs, comment/review activity
- Zero LLM token consumption while waiting (shell-level blocking)
- GitHub CLI integration with filtering by author and custom intervals

**Commands:**
- `/pr-watch` - Start monitoring PRs on the current repo

### brainstorm

Lightweight design-before-code discipline. Scales from one clarifying question to full collaborative design sessions.

**Install:**
```bash
/plugin install brainstorm@jai-cc-plugins
```

**Features:**
- Proportional design process: quick (1-2 exchanges), medium (3-6), or deep (7+)
- Avoids ceremony for simple tasks, enables full collaborative design for complex ones

**Skills:**
- `/brainstorm` - Start a design session before writing code

### claude-in-claude

Programmatic Claude Code CLI testing - structured JSON output parsing, multiturn session management, and isolation patterns for CI/containers.

**Install:**
```bash
/plugin install claude-in-claude@jai-cc-plugins
```

**Features:**
- Non-interactive Claude Code CLI invocation for scripts and automation
- Stream-JSON (JSONL) output format for structured parsing
- Session management with `--resume` for multiturn conversations
- Container-friendly with temp directory isolation
- Python reference implementation with async subprocess wrapper

**Skills:**
- `/claude-in-claude` - Guide for programmatic Claude Code usage
