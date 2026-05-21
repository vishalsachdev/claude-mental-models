# src/cmm/llm.py
"""Cached LLM wrapper that shells out to the local `claude` CLI.

Headless `claude -p` authenticates via the user's Claude subscription, so no
ANTHROPIC_API_KEY and no API credits are consumed.
"""
import json
import subprocess
import time

from cmm.cache import cached_call

MODEL = "claude-sonnet-4-6"  # capable + fast enough for hundreds of cached calls
_EMPTY_MCP = '{"mcpServers":{}}'  # disable MCP servers so each call stays lean
_MAX_RETRIES = 5  # transient CLI/rate-limit failures recover with backoff


def complete(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    """Return the model's text response. Cached by (system, prompt, model).

    `max_tokens` is part of the cache key for caller clarity but is not a hard
    CLI limit.
    """
    system = system or "You are a precise research assistant."
    key = "llm::" + json.dumps({"s": system, "p": prompt, "m": MODEL, "t": max_tokens})

    def run() -> str:
        """Invoke the claude CLI, retrying transient failures with backoff.

        Only a successful result is returned (and thus cached); after
        _MAX_RETRIES failures the error is raised.
        """
        last_err = ""
        for attempt in range(_MAX_RETRIES):
            try:
                proc = subprocess.run(
                    ["claude", "-p", "--output-format", "json",
                     "--strict-mcp-config", "--mcp-config", _EMPTY_MCP,
                     "--system-prompt", system, "--model", MODEL],
                    input=prompt, capture_output=True, text=True, timeout=300,
                )
                if proc.returncode != 0:
                    raise RuntimeError(f"rc={proc.returncode}: {proc.stderr.strip()}")
                envelope = json.loads(proc.stdout)
                if envelope.get("is_error"):
                    raise RuntimeError(f"is_error: {envelope.get('result')}")
                return envelope["result"]
            except (RuntimeError, subprocess.TimeoutExpired,
                    json.JSONDecodeError) as exc:
                last_err = str(exc)
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
        raise RuntimeError(
            f"claude CLI failed after {_MAX_RETRIES} attempts: {last_err}")

    return cached_call(key, run)


def complete_json(prompt: str, system: str = "", max_tokens: int = 2000):
    """Like `complete`, but parse the response as JSON.

    Strips a leading ```json fence if present.
    """
    raw = complete(prompt, system, max_tokens).strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(raw)
