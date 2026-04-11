#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
#     "websocket-client",
# ]
# ///
"""Sync claude.ai web conversations to local markdown files.

Uses the Chrome DevTools Protocol (CDP) to make API calls through a
running Chromium-based browser (Chrome, Brave, Edge, Chromium, Vivaldi,
Opera, etc.), bypassing Cloudflare's bot detection by reusing the
authenticated browser session. Conversations are saved as markdown with
YAML frontmatter.

Prerequisite: launch your browser with `--remote-debugging-port=9222`
and be logged into claude.ai in that browser.

Usage:
    claude-ai-sync.py [--out DIR] [--cdp-port PORT] [--log FILE]

The output directory defaults to $CLAUDE_AI_SYNC_OUT if set, else
./claude-ai-conversations. Sync state is stored in <out>/.sync-state.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import websocket


DEFAULT_CDP_PORT = 9222


def log(msg: str, log_file: Path | None = None) -> None:
    line = f"{datetime.now(timezone.utc).isoformat()} {msg}"
    print(msg, flush=True)
    if log_file:
        with log_file.open("a") as f:
            f.write(line + "\n")


def cdp_base(port: int) -> str:
    return f"http://localhost:{port}"


def get_cdp_connection(cdp_port: int) -> tuple[websocket.WebSocket, str]:
    """Connect to the browser via CDP and return (ws, org_id).

    Works with any Chromium-based browser launched with
    --remote-debugging-port=<cdp_port>. Prefers a claude.ai tab if open.
    """
    try:
        resp = requests.get(f"{cdp_base(cdp_port)}/json", timeout=5)
    except requests.exceptions.ConnectionError as e:
        raise RuntimeError(
            f"Cannot reach CDP on port {cdp_port}. Launch your browser with "
            f"--remote-debugging-port={cdp_port} and ensure you're logged into "
            f"claude.ai."
        ) from e
    pages = resp.json()
    if not pages:
        raise RuntimeError("CDP returned no browser pages")

    target = next((p for p in pages if "claude.ai" in p.get("url", "")), pages[0])
    ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=30)

    ws.send(json.dumps({
        "id": 1,
        "method": "Network.getCookies",
        "params": {"urls": ["https://claude.ai"]},
    }))
    result = json.loads(ws.recv())
    cookies = {c["name"]: c["value"] for c in result["result"]["cookies"]}
    org_id = cookies.get("lastActiveOrg")
    if not org_id:
        ws.close()
        raise RuntimeError(
            "No lastActiveOrg cookie found — not logged into claude.ai in this browser?"
        )

    current_url = target.get("url", "")
    if "claude.ai" not in current_url:
        ws.send(json.dumps({
            "id": 99,
            "method": "Page.navigate",
            "params": {"url": "https://claude.ai"},
        }))
        _drain_until(ws, 99)
        time.sleep(3)

    return ws, org_id


def cdp_fetch(ws: websocket.WebSocket, org_id: str, path: str, msg_id: int = 100) -> Any:
    """Fetch a claude.ai API path via the browser and return parsed JSON."""
    script = f"""
    (async () => {{
        const resp = await fetch('/api/organizations/{org_id}/{path}', {{
            credentials: 'include',
            headers: {{'Accept': 'application/json'}}
        }});
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        return JSON.stringify(await resp.json());
    }})()
    """
    ws.send(json.dumps({
        "id": msg_id,
        "method": "Runtime.evaluate",
        "params": {"expression": script, "awaitPromise": True, "returnByValue": True},
    }))
    result = _drain_until(ws, msg_id)
    exc = result.get("result", {}).get("exceptionDetails")
    if exc:
        raise RuntimeError(f"API error for {path}: {exc}")
    value = result["result"]["result"].get("value", "")
    return json.loads(value)


def _drain_until(ws: websocket.WebSocket, target_id: int) -> dict:
    for _ in range(50):
        msg = json.loads(ws.recv())
        if msg.get("id") == target_id:
            return msg
    raise RuntimeError(f"Timed out waiting for CDP response id={target_id}")


def load_state(state_file: Path) -> dict:
    if state_file.exists():
        return json.loads(state_file.read_text())
    return {"last_sync": None, "conversations": {}}


def save_state(state_file: Path, state: dict) -> None:
    state_file.write_text(json.dumps(state, indent=2))


def conversation_to_markdown(conv: dict) -> str:
    name = conv.get("name") or "Untitled"
    model = conv.get("model") or "unknown"
    created = conv.get("created_at", "")
    updated = conv.get("updated_at", "")
    uuid = conv.get("uuid", "")
    is_starred = conv.get("is_starred", False)
    summary = conv.get("summary") or ""

    lines = [
        "---",
        f"title: {json.dumps(name)}",
        f"uuid: {uuid}",
        f"model: {model}",
        f"created_at: {created}",
        f"updated_at: {updated}",
        f"is_starred: {str(is_starred).lower()}",
    ]
    if summary:
        lines.append(f"summary: {json.dumps(summary)}")
    lines.append("---")
    lines.append("")
    lines.append(f"# {name}")
    lines.append("")

    messages = conv.get("chat_messages") or []
    for msg in messages:
        sender = msg.get("sender", "unknown")
        text = msg.get("text", "")
        ts = msg.get("created_at", "")

        lines.append("## Human" if sender == "human" else "## Assistant")

        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                lines.append(f"*{dt.strftime('%Y-%m-%d %H:%M UTC')}*")
            except (ValueError, AttributeError):
                pass

        lines.append("")
        lines.append(text)
        lines.append("")

        attachments = msg.get("attachments") or []
        files = msg.get("files") or []
        if attachments:
            lines.append(f"*[{len(attachments)} attachment(s)]*")
            lines.append("")
        if files:
            for f in files:
                fname = f.get("file_name", "unknown")
                lines.append(f"*[File: {fname}]*")
            lines.append("")

    return "\n".join(lines)


def sanitize_filename(name: str) -> str:
    safe = "".join(c if c.isalnum() or c in " -_" else "_" for c in name)
    return safe.strip()[:80] or "untitled"


def rebuild_name_index(out_dir: Path, conversations: list[dict]) -> None:
    index_dir = out_dir / "by-name"
    index_dir.mkdir(exist_ok=True)
    for link in index_dir.iterdir():
        if link.is_symlink():
            link.unlink()
    for conv in conversations:
        uuid = conv["uuid"]
        name = sanitize_filename(conv.get("name") or "Untitled")
        md_file = out_dir / f"{uuid}.md"
        if not md_file.exists():
            continue
        link = index_dir / f"{name}.md"
        counter = 1
        while link.exists():
            link = index_dir / f"{name}_{counter}.md"
            counter += 1
        link.symlink_to(f"../{uuid}.md")


def run(out_dir: Path, cdp_port: int, log_file: Path | None) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    state_file = out_dir / ".sync-state.json"
    state = load_state(state_file)
    known = state.get("conversations", {})

    log("Connecting to browser via CDP...", log_file)
    ws, org_id = get_cdp_connection(cdp_port)
    log(f"Connected. Org: {org_id}", log_file)

    log("Fetching conversation list...", log_file)
    conversations = cdp_fetch(ws, org_id, "chat_conversations", msg_id=10)
    log(f"Found {len(conversations)} conversations", log_file)

    to_sync = [
        c for c in conversations
        if known.get(c["uuid"]) != c.get("updated_at", "")
    ]
    log(f"{len(to_sync)} new/updated since last sync", log_file)

    synced = 0
    errors = 0
    for i, conv in enumerate(to_sync):
        uuid = conv["uuid"]
        name = conv.get("name") or "Untitled"
        try:
            full = cdp_fetch(ws, org_id, f"chat_conversations/{uuid}", msg_id=200 + i)
            md = conversation_to_markdown(full)
            (out_dir / f"{uuid}.md").write_text(md)
            known[uuid] = conv.get("updated_at", "")
            synced += 1

            if (i + 1) % 25 == 0:
                log(f"  Progress: {i + 1}/{len(to_sync)}", log_file)
                state["conversations"] = known
                save_state(state_file, state)

            time.sleep(0.15)

        except Exception as e:
            log(f"  Error syncing '{name}' ({uuid}): {e}", log_file)
            errors += 1
            try:
                ws.ping()
            except Exception:
                log("  Reconnecting CDP...", log_file)
                try:
                    ws.close()
                except Exception:
                    pass
                ws, org_id = get_cdp_connection(cdp_port)

    ws.close()

    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    state["conversations"] = known
    save_state(state_file, state)

    rebuild_name_index(out_dir, conversations)

    log(f"Done. Synced {synced}, errors {errors}, total tracked {len(known)}", log_file)
    return 1 if errors and synced == 0 else 0


def main() -> int:
    default_out = os.environ.get("CLAUDE_AI_SYNC_OUT") or str(Path.cwd() / "claude-ai-conversations")
    parser = argparse.ArgumentParser(description="Sync claude.ai conversations to local markdown.")
    parser.add_argument("--out", default=default_out, help="Output directory (default: $CLAUDE_AI_SYNC_OUT or ./claude-ai-conversations)")
    parser.add_argument("--cdp-port", type=int, default=DEFAULT_CDP_PORT, help=f"CDP port (default: {DEFAULT_CDP_PORT})")
    parser.add_argument("--log", default=None, help="Optional log file path")
    args = parser.parse_args()

    log_file = Path(args.log) if args.log else None
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        return run(Path(args.out), args.cdp_port, log_file)
    except Exception as e:
        log(f"FATAL: {e}", log_file)
        return 2


if __name__ == "__main__":
    sys.exit(main())
