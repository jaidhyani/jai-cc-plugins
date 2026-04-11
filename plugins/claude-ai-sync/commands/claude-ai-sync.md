---
description: Sync claude.ai web conversations to local markdown files
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/*), Bash(command -v *), Bash(curl -s *)
---

# Claude.ai Sync

Pull the user's claude.ai web conversations into local markdown files via CDP through their running browser.

## Preflight

1. Check `uv` is on PATH — if missing, tell the user to install it and stop.
2. Check the browser is reachable at `http://localhost:9222/json/version` — if not, tell the user to launch their browser with `--remote-debugging-port=9222` and stop.

## Run

Pick the output directory in priority order:
1. `$CLAUDE_AI_SYNC_OUT` if set.
2. Otherwise ask the user where they want conversations stored (or use `~/claude-ai-conversations` as a default).

Run:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/claude-ai-sync.py --out "$OUT_DIR"
```

## Report

After the script exits, report:
- How many conversations were synced vs skipped.
- Any errors from the script's output.
- The location of the output directory.
- If this was a first run, note that subsequent runs will be incremental.

If the script exited non-zero, surface the error message verbatim — the script's errors are already diagnostic.
