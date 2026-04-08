# Claude Code Plugin Marketplace

This is Jai's personal plugin marketplace for Claude Code plugins.

## Adding a New Plugin

Two steps required:

1. **Create plugin files** in `plugins/<plugin-name>/`
2. **Register in marketplace** by adding an entry to `.claude-plugin/marketplace.json`

Without step 2, the plugin won't appear when users browse the marketplace.

## Marketplace Registration

Every plugin must be listed in `.claude-plugin/marketplace.json` to be discoverable. Without an entry there, Claude Code can't find the plugin even if the files exist on disk. When adding a new plugin, always add both the directory and the manifest entry.

## Plugin Structure

Each plugin lives in `plugins/<plugin-name>/` with:
- `.claude-plugin/plugin.json` - manifest with name, version, description
- `hooks/hooks.json` - hook definitions (if using hooks)
- `hooks/*.sh` - hook scripts
- `commands/*.md` - slash commands
- `skills/*.md` - skills

## Hooks

### hooks.json Structure

**IMPORTANT:** The hooks.json file MUST have a top-level `hooks` key wrapping the event types.

Correct structure:
```json
{
  "hooks": {
    "EventName": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/script.sh"
          }
        ]
      }
    ]
  }
}
```

Wrong (missing `hooks` wrapper):
```json
{
  "EventName": [...]
}
```

### Hook Events

Available events: `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreCompact`, `Notification`

### Session-Specific State

Hooks receive JSON input on stdin with `session_id`. Use this for session-specific state files:

```bash
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "default"')
STATE_FILE="/tmp/myplugin-${SESSION_ID}.txt"
```

Never use a single global file for state that should be per-session.

## README

**Always update README.md when adding, removing, or changing plugins.** The README is the public-facing plugin catalog — it must stay in sync with `marketplace.json`.

## Versioning

**Always bump the version in `plugin.json` when a plugin changes.** Users won't get updates without a version bump.

Semantic versioning:
- **0.0.1** - Bugfixes (no new features, no breaking changes)
- **0.1.0** - New features (backwards compatible)
- **1.0.0** - Breaking changes
