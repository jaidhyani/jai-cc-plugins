---
name: claude-ai-sync
description: This skill should be used when the user asks to "sync claude.ai chats", "export claude.ai conversations", "backup my claude web history", "save claude conversations locally", "download claude.ai chats", "set up claude.ai sync", "install claude-ai-sync", "run the claude.ai export", or mentions wanting local markdown copies of their claude.ai web conversations. Handles first-time setup, on-demand runs, and troubleshooting.
---

# claude-ai-sync

Pulls the user's claude.ai web conversations into local markdown files by calling claude.ai's internal API **through a running Chromium-based browser** via the Chrome DevTools Protocol (CDP). This reuses the authenticated browser session so Cloudflare bot detection doesn't block it — plain `curl` will not work.

Output: one `<uuid>.md` per conversation with YAML frontmatter (title, model, timestamps, starred), plus a `by-name/` directory of symlinks for human browsing, plus a `.sync-state.json` that tracks which conversations have already been fetched (so subsequent runs are incremental).

## Prerequisites

1. **A Chromium-based browser running with remote debugging.** Any of Chrome, Brave, Chromium, Edge, Vivaldi, Opera works — they all speak the same CDP. Launch with:
   ```
   --remote-debugging-port=9222
   ```
   The user should make this part of how they normally launch the browser. It's safe (localhost-only by default) and required for the sync to work at all.

2. **Logged into claude.ai** in that browser. The sync reads the `lastActiveOrg` cookie to pick the target organization.

3. **`uv` installed.** The sync script uses PEP 723 inline script metadata so `uv run --script` handles dependencies — no manual pip install. If `uv` isn't present, install it via `pipx install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`.

## When this applies

- First-time install on a machine.
- Running a sync on demand ("pull my latest claude chats").
- Diagnosing "the sync isn't working" — almost always a browser or CDP issue.
- Adding this to a nightly cron.
- Moving the output directory.

## Files this plugin ships

- `scripts/claude-ai-sync.py` — self-contained Python script. Single file. Uses PEP 723 shebang (`#!/usr/bin/env -S uv run --script`) so dependencies (`requests`, `websocket-client`) are managed automatically. No separate shell wrapper needed.
- `commands/claude-ai-sync.md` — slash command that runs the sync.

## The script's interface

```
claude-ai-sync.py [--out DIR] [--cdp-port PORT] [--log FILE]
```

- `--out DIR`: where to write conversations. Defaults to `$CLAUDE_AI_SYNC_OUT` env var, else `./claude-ai-conversations`.
- `--cdp-port PORT`: CDP port the browser is listening on. Default 9222.
- `--log FILE`: optional append-only log file. Every line also goes to stdout.

Exit codes: `0` success (even if no new conversations), `1` partial failure (errors but some synced), `2` fatal (couldn't connect to CDP or similar).

## Install workflow

### Step 1: Confirm prerequisites
- Ask the user (or verify) which browser they use as their daily driver and whether they launch it with `--remote-debugging-port=9222`. If not, help them make that permanent. Concrete examples:
    - **Linux desktop (.desktop file):** edit `~/.local/share/applications/<browser>.desktop`, change the `Exec=` line to append `--remote-debugging-port=9222` at the end of the command. For Brave: `Exec=/usr/bin/brave-browser --remote-debugging-port=9222 %U`.
    - **macOS shell alias:** `alias brave='open -a "Brave Browser" --args --remote-debugging-port=9222'` in `~/.zshrc`.
    - **Windows shortcut:** edit the browser shortcut's Target field to append ` --remote-debugging-port=9222`.
- Verify `uv` is on PATH: `command -v uv`. If missing, install it via `curl -LsSf https://astral.sh/uv/install.sh | sh` or `pipx install uv`.
- Verify they can reach `http://localhost:9222/json/version` while the browser is running — that's the CDP handshake endpoint. If this fails, no sync will work.

### Step 2: Pick an output directory
Default is `~/claude-ai-conversations/`, but if the user has a notes repo or data directory, put it there. Common choices:
- `~/claude-ai-conversations` (standalone)
- `<notes-repo>/data/claude-ai-conversations` (versioned alongside notes)
- `<clai-style-repo>/data/claude-ai-conversations` (alongside other synced data)

Either pass `--out` explicitly every time, or set `CLAUDE_AI_SYNC_OUT` in their shell profile.

### Step 3: Copy the script into the target location
Copy the script from the plugin to a convenient location on the target machine — often `<repo>/scripts/claude-ai-sync.py` — and `chmod +x` it.

Find the script in this order:
1. `${CLAUDE_PLUGIN_ROOT}/scripts/claude-ai-sync.py` — set when the skill is invoked via an installed plugin.
2. If that env var isn't set, search with `find ~/.claude/plugins -name claude-ai-sync.py -type f 2>/dev/null | head -1`.
3. If still not found, Read the SKILL.md you're reading now — the plugin directory is its grandparent. The script is at `../../scripts/claude-ai-sync.py` relative to this file.

Alternatively, skip the copy and invoke the script directly from the plugin cache — but most users prefer it lives in their own repo so it's versioned alongside their notes.

### Step 4: First run
Run it once to populate the full history:

```bash
./claude-ai-sync.py --out "$OUT_DIR"
```

Expected output: connects via CDP, reports conversation count (can be hundreds or thousands), syncs new/updated, writes `<out>/<uuid>.md` files and a `by-name/` symlink directory. First run on a fresh install takes time (one HTTP fetch per conversation, ~150ms throttle each) — for 1000 conversations, budget 3–5 minutes.

If it fails on connect, the error message will say exactly what's wrong (port unreachable, no claude.ai cookie, etc.). Fix the prerequisite and retry.

### Step 5: (optional) Schedule it
If the user wants automatic syncs, add it to cron. **The browser must be running when cron fires**, so a nightly schedule works well for someone who leaves their machine on; a schedule during typical active hours works for people who shut down at night.

Example crontab line:
```
17 2 * * * /path/to/claude-ai-sync.py --out /path/to/out --log /path/to/sync.log >> /path/to/cron.log 2>&1
```

If cron can't find `uv` (common — cron's PATH is minimal), use the `cron-safe` skill to set up a shared `lib/cron-env.sh` for this and other cron scripts. Alternatively, invoke the script with an absolute path to a wrapper that sources your shell profile.

### Step 6: Verify
After a successful run, confirm:
- `ls <out>/*.md | wc -l` matches roughly the conversation count
- `<out>/.sync-state.json` exists and has a recent `last_sync`
- `<out>/by-name/` has readable symlinks

## On-demand run

If the user just wants a one-off sync and the script is already installed, run it:

```bash
<path>/claude-ai-sync.py --out "$CLAUDE_AI_SYNC_OUT"
```

Or use the `/claude-ai-sync` slash command if the plugin is installed and the path is known.

## Troubleshooting

- **`Cannot reach CDP on port 9222`** — the browser isn't running with the debugging flag. Relaunch with `--remote-debugging-port=9222`.
- **`No lastActiveOrg cookie found`** — not logged into claude.ai in that browser. Log in, refresh, retry.
- **`HTTP 403` or similar on individual conversations** — Cloudflare is rate-limiting. The script already throttles at 150ms/conv; if it's still too fast, increase the `time.sleep(0.15)` in the per-conversation loop.
- **Cron fires but fails** — check the log file. If it says `uv: command not found`, cron PATH is wrong. Invoke `cron-safe` skill.
- **Sync seems stuck or errored mid-run** — re-run it. The state file is persisted incrementally, so a second run skips already-fetched conversations and picks up where the last one left off.
- **Changed `--out` on a re-run** — the state file lives inside the output directory (`<out>/.sync-state.json`), so pointing at a new directory triggers a full re-sync. Either move the state file along with the output, or accept the full re-download.

## Anti-patterns

- **Don't try to call claude.ai's API directly with `curl` or `requests` from outside the browser.** Cloudflare will block you. CDP through the authenticated browser is the whole point.
- **Don't store or copy the session cookie elsewhere.** Reading cookies via CDP each run is the simplest and safest — no secrets on disk.
- **Don't shell-wrap this script unless you need env setup for cron.** The Python script handles its own dependencies via PEP 723; a shell wrapper adds a file to maintain and gains you nothing.
