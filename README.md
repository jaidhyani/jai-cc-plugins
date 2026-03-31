# jai-cc-plugins

Claude Code plugins.

```bash
/plugin marketplace add jaidhyani/jai-cc-plugins
```

## Plugins

| Plugin | Type | Description |
|--------|------|-------------|
| [ultrapowers](#ultrapowers) | Skills | Brainstorming, debugging, TDD, verification, planning, code review, agents |
| [devil](#devil) | Agent | Find flaws in plans, designs, and code |
| [brainstorm](#brainstorm) | Skill | Think before coding |
| [imagine](#imagine) | Command | Generate images with Gemini 3 Pro |
| [pr-watch](#pr-watch) | Command | Block until PRs change |
| [claude-archivist](#claude-archivist) | Hooks | Back up session transcripts |
| [timestamp-tracker](#timestamp-tracker) | Hooks | Track prompt/response timestamps |
| [claude-in-claude](#claude-in-claude) | Skill | Run Claude Code from scripts |

---

### ultrapowers

Opinionated dev workflow skills. Fork of the official [superpowers](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/superpowers) plugin.

```bash
/plugin install ultrapowers@jai-cc-plugins
```

| Skill | |
|-------|-|
| `/ultrapowers:brainstorm` | Design before code |
| `/ultrapowers:debugging` | Root-cause investigation |
| `/ultrapowers:tdd` | Red-green-refactor |
| `/ultrapowers:verify` | Check work before claiming done |
| `/ultrapowers:plans` | Write and execute implementation plans |
| `/ultrapowers:code-review` | Review and address feedback |
| `/ultrapowers:agents` | Parallel and sequential task dispatch |

### devil

Tears apart plans, designs, and code. Reads the actual codebase and builds counterexamples. One fatal flaw > twenty style nits.

```bash
/plugin install devil@jai-cc-plugins
```

**Skill:** `/devil`

Output formats: structured teardown, Socratic questioning, rapid-fire concerns, or single fatal flaw.

### brainstorm

Ask questions before writing code. Scales up with complexity: 1-2 exchanges for simple stuff, 7+ for hard problems.

```bash
/plugin install brainstorm@jai-cc-plugins
```

**Skill:** `/brainstorm`

### imagine

Generate images with Gemini 3 Pro.

```bash
/plugin install imagine@jai-cc-plugins
```

**Command:** `/imagine`

Aspect ratios: 1:1, 16:9, 9:16, 4:3, 3:4. Sizes: 1K, 2K, 4K. Optional reference image. Defaults to 1:1 @ 2K.

### pr-watch

Polls GitHub for PR changes and blocks until something happens. No tokens burned while waiting.

```bash
/plugin install pr-watch@jai-cc-plugins
```

**Command:** `/pr-watch`

Detects new commits, status changes, merges, new PRs, comments, and reviews. Filter by author, set custom intervals.

### claude-archivist

Backs up session transcripts to `~/.claude-archive/`. Runs on SessionEnd, PreCompact, and periodically. Incremental, gzip-compressed.

```bash
/plugin install claude-archivist@jai-cc-plugins
```

| Command | |
|---------|-|
| `/claude-archivist:archive` | Archive current session |
| `/claude-archivist:archive-all` | Archive all sessions |
| `/claude-archivist:archive-status` | Show stats |
| `/claude-archivist:restore-from-archive` | Restore deleted sessions |
| `/claude-archivist:configure-archive` | Configure |

<details>
<summary>Configuration</summary>

Create `~/.claude/claude-archivist.local.md`:
```yaml
---
archive_path: ~/.claude-archive
backup_interval_minutes: 30
enabled: true
---
```
</details>

### timestamp-tracker

Records timestamps on every prompt and response via hooks. No commands, just runs in the background.

```bash
/plugin install timestamp-tracker@jai-cc-plugins
```

### claude-in-claude

Guide for running Claude Code non-interactively: JSON output parsing, `--resume` for multiturn, container isolation.

```bash
/plugin install claude-in-claude@jai-cc-plugins
```

**Skill:** `/claude-in-claude`
