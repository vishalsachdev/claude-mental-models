# src/cmm/collect_changelog.py
"""Collect and parse the Claude Code CHANGELOG.md."""
import hashlib
import re
import subprocess
from pathlib import Path

REPO_URL = "https://github.com/anthropics/claude-code.git"
VERSION_RE = re.compile(r"^##\s+v?(\d+\.\d+\.\d+\S*)\s*$")
BULLET_RE = re.compile(r"^[-*]\s+(.*\S)\s*$")

_RULES = [
    ("deprecate", ("deprecat",)),
    ("remove", ("removed", "remove ", "deleted")),
    ("add", ("added", "add ", "new ", "introduc")),
    ("fix", ("fixed", "fix ", "bug")),
]


def classify_change(text: str) -> str:
    """Map a changelog entry to a change_type via keyword rules."""
    low = text.lower()
    for label, keywords in _RULES:
        if any(k in low for k in keywords):
            return label
    return "change"


def _entry_id(version: str, text: str) -> str:
    return hashlib.sha256(f"{version}|{text}".encode()).hexdigest()[:12]


def parse_changelog(markdown: str) -> list[dict]:
    """Parse CHANGELOG.md text into a list of entry dicts.

    Each dict: {id, version, text, change_type}. Raises ValueError if a
    bullet appears before any version heading (structure changed upstream).
    """
    entries: list[dict] = []
    current: str | None = None
    for lineno, line in enumerate(markdown.splitlines(), 1):
        vm = VERSION_RE.match(line)
        if vm:
            current = vm.group(1)
            continue
        bm = BULLET_RE.match(line)
        if bm:
            if current is None:
                raise ValueError(f"Bullet before any version heading at line {lineno}")
            text = bm.group(1)
            entries.append({
                "id": _entry_id(current, text),
                "version": current,
                "text": text,
                "change_type": classify_change(text),
            })
    if not entries:
        raise ValueError("No changelog entries parsed — upstream format may have changed")
    return entries


def clone_or_update_repo(dest: Path) -> Path:
    """Clone anthropics/claude-code (or fetch if already present)."""
    dest = Path(dest)
    if (dest / ".git").exists():
        subprocess.run(["git", "-C", str(dest), "fetch", "--all"], check=True)
    else:
        subprocess.run(["git", "clone", "--depth", "1000", REPO_URL, str(dest)], check=True)
    return dest
