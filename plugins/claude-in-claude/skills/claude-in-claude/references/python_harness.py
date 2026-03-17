"""Reference implementation: async Python harness for programmatic Claude Code CLI testing.

Provides dataclasses for parsing stream-json output, an async subprocess wrapper,
and a multiturn session resume pattern.

Adapt to your project — this is a starting point, not a library.
"""

import asyncio
import json
import os
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class ClaudeCodeEvent:
    """A parsed event from claude stream-json output."""

    type: str
    subtype: str | None = None
    raw: dict = field(default_factory=dict)

    @property
    def is_init(self) -> bool:
        return self.type == "system" and self.subtype == "init"

    @property
    def is_assistant(self) -> bool:
        return self.type == "assistant"

    @property
    def is_user(self) -> bool:
        return self.type == "user"

    @property
    def is_result(self) -> bool:
        return self.type == "result"

    @property
    def is_success(self) -> bool:
        return self.is_result and self.subtype == "success"

    @property
    def is_error(self) -> bool:
        return self.is_result and self.raw.get("is_error", False)

    def get_tool_uses(self) -> list[dict]:
        if not self.is_assistant:
            return []
        content = self.raw.get("message", {}).get("content", [])
        return [b for b in content if isinstance(b, dict) and b.get("type") == "tool_use"]

    def get_tool_results(self) -> list[dict]:
        if not self.is_user:
            return []
        content = self.raw.get("message", {}).get("content", [])
        return [b for b in content if isinstance(b, dict) and b.get("type") == "tool_result"]

    def get_text_content(self) -> str:
        if not self.is_assistant:
            return ""
        content = self.raw.get("message", {}).get("content", [])
        return " ".join(
            b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
        )


@dataclass
class ClaudeCodeResult:
    """Complete result of a claude CLI invocation."""

    events: list[ClaudeCodeEvent]
    final_result: str
    is_success: bool
    num_turns: int
    cost_usd: float
    session_id: str
    raw_output: str
    stderr: str

    @property
    def init_event(self) -> ClaudeCodeEvent | None:
        return next((e for e in self.events if e.is_init), None)

    @property
    def tool_uses(self) -> list[dict]:
        uses = []
        for event in self.events:
            uses.extend(event.get_tool_uses())
        return uses

    @property
    def tool_results(self) -> list[dict]:
        results = []
        for event in self.events:
            results.extend(event.get_tool_results())
        return results

    def tools_used(self) -> set[str]:
        return {use.get("name", "") for use in self.tool_uses}


def parse_stream_json(output: str) -> list[ClaudeCodeEvent]:
    """Parse JSONL stream-json output into typed events.

    Gracefully skips non-JSON lines (startup banners, warnings).
    """
    events = []
    for line in output.strip().split("\n"):
        if not line:
            continue
        try:
            data = json.loads(line)
            events.append(
                ClaudeCodeEvent(
                    type=data.get("type", "unknown"),
                    subtype=data.get("subtype"),
                    raw=data,
                )
            )
        except json.JSONDecodeError:
            continue
    return events


async def run_claude_code(
    prompt: str,
    *,
    max_turns: int = 5,
    timeout_seconds: int = 120,
    base_url: str | None = None,
    api_key: str | None = None,
    system_prompt: str | None = None,
    working_dir: str | None = None,
    resume_session_id: str | None = None,
    allowed_tools: list[str] | None = None,
    tools: list[str] | None = None,
) -> ClaudeCodeResult:
    """Run claude CLI in print mode and parse output.

    Set base_url to route through a proxy/gateway.
    Set resume_session_id to continue an existing session.
    """
    cmd = ["claude", "-p", "--output-format", "stream-json", "--verbose"]

    if allowed_tools:
        cmd.extend(["--permission-mode", "dontAsk", "--allowedTools"] + allowed_tools)

    if resume_session_id:
        cmd.extend(["--resume", resume_session_id])

    if tools:
        cmd.extend(["--tools", " ".join(tools)])

    cmd.extend(["--max-turns", str(max_turns)])

    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    env = os.environ.copy()
    if base_url:
        env["ANTHROPIC_BASE_URL"] = base_url
    if api_key:
        env["ANTHROPIC_API_KEY"] = api_key
    env.pop("CLAUDECODE", None)
    env.pop("CLAUDE_CODE_ENTRYPOINT", None)

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
        cwd=working_dir,
    )

    stdout, stderr = await asyncio.wait_for(
        proc.communicate(prompt.encode()),
        timeout=timeout_seconds,
    )

    raw_output = stdout.decode()
    stderr_output = stderr.decode()
    events = parse_stream_json(raw_output)

    final_result = ""
    is_success = False
    num_turns = 0
    cost_usd = 0.0
    session_id = ""

    for event in events:
        if not event.is_result:
            continue
        final_result = event.raw.get("result", "")
        is_success = event.is_success
        num_turns = event.raw.get("num_turns", 0)
        cost_usd = event.raw.get("total_cost_usd", 0.0)
        session_id = event.raw.get("session_id", "")

    return ClaudeCodeResult(
        events=events,
        final_result=final_result,
        is_success=is_success,
        num_turns=num_turns,
        cost_usd=cost_usd,
        session_id=session_id,
        raw_output=raw_output,
        stderr=stderr_output,
    )


# --- Example usage ---

async def example_multiturn():
    """Demonstrates a 3-turn session with /compact."""

    # Turn 1: Do work
    step1 = await run_claude_code(
        prompt="Create a file called hello.txt containing 'hello world'",
        allowed_tools=["Write", "Read"],
        max_turns=3,
        working_dir="/tmp/claude-test",
    )
    assert step1.is_success
    assert step1.session_id

    # Turn 2: Compact context
    step2 = await run_claude_code(
        prompt="/compact",
        max_turns=1,
        resume_session_id=step1.session_id,
        working_dir="/tmp/claude-test",
    )

    # Turn 3: Verify session still works
    step3 = await run_claude_code(
        prompt="What file did you create? Reply briefly.",
        max_turns=1,
        resume_session_id=step1.session_id,
        working_dir="/tmp/claude-test",
    )
    assert step3.is_success
    assert step3.final_result


if __name__ == "__main__":
    asyncio.run(example_multiturn())
