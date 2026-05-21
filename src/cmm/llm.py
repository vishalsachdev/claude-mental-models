# src/cmm/llm.py
"""Cached LLM wrapper that shells out to the local `claude` CLI.

Headless `claude -p` authenticates via the user's Claude subscription, so no
ANTHROPIC_API_KEY and no API credits are consumed.
"""
import json
import re
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


def _extract_json(text: str):
    """Parse JSON from a model response, tolerating fences and surrounding prose."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0] if "\n" in text else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Fallback: grab the outermost {...} or [...] block.
    m = re.search(r"\{.*\}|\[.*\]", text, re.S)
    if m:
        return json.loads(m.group(0))
    raise ValueError(f"no JSON found in response: {text[:200]!r}")


def complete_json(prompt: str, system: str = "", max_tokens: int = 2000,
                  retries: int = 3):
    """Like `complete`, but parse the response as JSON.

    Tolerates ```json fences and prose around the JSON. If the response is not
    parseable, retries with a cache-busting nudge (a fresh model call) up to
    `retries` times before raising.
    """
    last_exc: Exception | None = None
    for attempt in range(retries):
        # Append the nudge `attempt` times so each retry is a distinct cache
        # key (a fresh model call), not a re-read of the bad cached response.
        p = prompt + "\n\n(Respond with valid JSON only — no prose.)" * attempt
        raw = complete(p, system, max_tokens)
        try:
            return _extract_json(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            last_exc = exc
    raise RuntimeError(f"complete_json failed after {retries} attempts: {last_exc}")
