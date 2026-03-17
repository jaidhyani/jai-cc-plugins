---
name: claude-in-claude
description: This skill should be used when the user asks to "test claude code", "run claude programmatically", "claude-in-claude", "automate claude", "spawn a new claude session", "run claude code autonomously", "multiturn claude testing", "use claude cli in a script", "parse claude output", "claude subprocess", or needs to invoke the Claude Code CLI non-interactively with structured JSON output, session management, and multiturn resume.
---

# Claude-in-Claude: Programmatic Claude Code Testing

Run the Claude Code CLI non-interactively from scripts or test harnesses, parse structured JSON output, and chain multiturn sessions via `--resume`.

## Core CLI Invocation

```bash
claude -p --output-format stream-json --verbose \
  --max-turns 5 \
  --permission-mode dontAsk \
  --allowedTools Read Write Bash
```

**Key flags:**

| Flag | Purpose |
|------|---------|
| `-p` | Print mode — non-interactive, reads prompt from stdin |
| `--output-format stream-json` | JSONL output, one JSON object per line |
| `--verbose` | Include detailed event metadata |
| `--max-turns N` | Cap agentic turns (one turn = model response + tool execution cycle) |
| `--resume <session_id>` | Continue an existing session |
| `--system-prompt "..."` | Override system prompt |
| `--permission-mode dontAsk` | Skip permission prompts |
| `--allowedTools Tool1 Tool2` | Permission whitelist — restricts which tools can run (requires `dontAsk`) |
| `--tools "Tool1 Tool2"` | Capability enablement — makes tools available to the model |

Prompt is piped via **stdin**, not as a positional argument.

## Environment Variables

```bash
# Route to a custom endpoint (proxy, gateway, mock server)
export ANTHROPIC_BASE_URL="http://localhost:8000"
export ANTHROPIC_API_KEY="sk-your-key"

# Clean env to avoid interfering with nested Claude instances
unset CLAUDECODE
unset CLAUDE_CODE_ENTRYPOINT
```

Setting `ANTHROPIC_BASE_URL` routes all API calls through that endpoint — useful for proxies, gateways, or test servers. Unsetting `CLAUDECODE` and `CLAUDE_CODE_ENTRYPOINT` prevents the child Claude from inheriting parent session state.

## Stream-JSON Output Format

Each line of stdout is a JSON object with a `type` field:

| type | subtype | Contains |
|------|---------|----------|
| `system` | `init` | Session metadata, model info |
| `assistant` | — | Model response with `content` blocks (text, tool_use) |
| `user` | — | Tool results with `content` blocks (tool_result) |
| `result` | `success`/`error` | Final result, `session_id`, `num_turns`, `total_cost_usd` |

### Extracting Session ID

The `result` event contains `session_id` — essential for `--resume`:

```python
for event in events:
    if event["type"] == "result":
        session_id = event["session_id"]
        is_success = event["subtype"] == "success"
        final_text = event["result"]
```

### Extracting Tool Use

Tool calls appear in `assistant` events, results in `user` events:

```python
# From assistant event
tool_uses = [b for b in event["message"]["content"]
             if b.get("type") == "tool_use"]

# From user event
tool_results = [b for b in event["message"]["content"]
                if b.get("type") == "tool_result"]
```

## Multiturn Sessions

Chain multiple turns by extracting `session_id` and passing `--resume`:

```
Turn 1:  claude -p ...              → parse result → extract session_id
Turn 2:  claude -p --resume <id>    → new prompt via stdin
Turn 3:  claude -p --resume <id>    → continues same conversation
```

Send `/compact` as a prompt between turns to compress context when the conversation grows large.

## Isolation & Containerization

For hermetic test runs, isolate each session:

- **Working directory**: Pass `cwd` to subprocess to scope file operations to a temp directory
- **Temp dirs**: Use per-test temp directories so file operations don't leak across tests
- **Unique IDs**: Generate a unique test ID per run to avoid collisions
- **Container-friendly**: The CLI is a Node process — runs in any container with Node installed. Mount only the working directory. Set env vars for API routing.

```bash
# Docker example
docker run --rm \
  -e ANTHROPIC_API_KEY="$KEY" \
  -e ANTHROPIC_BASE_URL="http://host.docker.internal:8000" \
  -v "$TMPDIR:/workspace" \
  -w /workspace \
  node-with-claude \
  sh -c 'echo "What is 2+2?" | claude -p --output-format stream-json --max-turns 1'
```

## Reference Implementation

See `references/python_harness.py` for a complete async Python implementation with:
- `ClaudeCodeEvent` / `ClaudeCodeResult` dataclasses
- `parse_stream_json()` JSONL parser
- `run_claude_code()` async subprocess wrapper with timeout
- Multiturn session resume pattern

## Practical Tips

- **Timeouts**: Set generous timeouts (120s+) for turns with tool use. Use `asyncio.wait_for` or equivalent.
- **stderr**: Capture stderr separately — it contains debug logs and error details.
- **Graceful JSON errors**: Some lines may not be valid JSON (startup banners, warnings). Skip `JSONDecodeError` lines.
- **Cost tracking**: The result event includes `total_cost_usd` — useful for test budgets.
- **Max turns**: Start with `max_turns=1` for simple Q&A, increase for tool-heavy tasks.
