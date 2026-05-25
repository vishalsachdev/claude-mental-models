# src/cmm/codex_llm.py
"""Cached LLM wrapper that shells out to the local `codex exec` CLI.

Used only for the B3 independent derivation (GPT-5.5). Codex is an agentic
CLI, not a JSON endpoint, so responses are parsed leniently and every call is
cached — the cached output is committed so B3 never re-runs nondeterministically.

CLAUDE.md gotcha: never pipe codex output through `tail` (deadlocks 30+ min).
`subprocess.run(capture_output=True)` reads directly, so it is safe.
"""
import json
import re
import subprocess
import time

from cmm.cache import cached_call

MODEL = "gpt-5.5"          # pinned: the independent derivation's model
_TIMEOUT = 600             # codex can be slow; generous one-shot timeout
_MAX_RETRIES = 3


def extract_json(text: str):
    """Parse JSON from a codex response, tolerating fences and surrounding prose."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0] if "\n" in text else text
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}|\[.*\]", text, re.S)
    if m:
        return json.loads(m.group(0))
    raise ValueError(f"no JSON found in codex response: {text[:200]!r}")


def complete_json(prompt: str, system: str = "", max_tokens: int = 2000):
    """Run `codex exec` with the given prompt; return parsed JSON. Cached.

    `max_tokens` only varies the cache key. The prompt is prefixed with the
    system instruction and an explicit JSON-only directive because codex has
    no separate system-prompt flag.
    """
    system = system or "You are a precise qualitative-research assistant."
    full = (f"{system}\n\n{prompt}\n\n"
            "Respond with valid JSON only. Do not run tools, do not read or "
            "modify files, do not print anything except the JSON object.")
    key = "codex::" + json.dumps({"p": full, "m": MODEL, "t": max_tokens})

    def run():
        last_err = ""
        for attempt in range(_MAX_RETRIES):
            try:
                proc = subprocess.run(
                    ["codex", "exec", "--sandbox", "read-only",
                     "--model", MODEL, full],
                    capture_output=True, text=True, timeout=_TIMEOUT,
                    # stdin=DEVNULL: codex exec reads stdin even with a
                    # positional prompt; if the parent has a TTY or open pipe,
                    # codex blocks waiting for additional input forever.
                    stdin=subprocess.DEVNULL,
                )
                if proc.returncode != 0:
                    raise RuntimeError(f"rc={proc.returncode}: {proc.stderr.strip()}")
                return extract_json(proc.stdout)
            except (RuntimeError, ValueError, json.JSONDecodeError,
                    subprocess.TimeoutExpired) as exc:
                last_err = str(exc)
                if attempt < _MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
        raise RuntimeError(f"codex exec failed after {_MAX_RETRIES}: {last_err}")

    return cached_call(key, run)
