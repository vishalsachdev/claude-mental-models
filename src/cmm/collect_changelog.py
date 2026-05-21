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
    ("deprecate", r"\bdeprecat\w*"),
    ("remove", r"\b(remove[sd]?|deleted)\b"),
    ("add", r"\b(adds?|added|new|introduc\w*)\b"),
    ("fix", r"\b(fix(es|ed)?|bugs?)\b"),
]


def classify_change(text: str) -> str:
    """Map a changelog entry to a change_type via word-boundary keyword rules."""
    low = text.lower()
    for label, pattern in _RULES:
        if re.search(pattern, low):
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


def version_dates(repo: Path) -> dict[str, str]:
    """Map version -> ISO date of the commit that first added its heading.

    Walks `git log` of CHANGELOG.md oldest-first; the first commit whose diff
    adds `## <version>` dates that version.
    """
    repo = Path(repo)
    log = subprocess.run(
        ["git", "-C", str(repo), "log", "--reverse", "--date=short",
         "--format=%H%x09%ad", "--", "CHANGELOG.md"],
        check=True, capture_output=True, text=True,
    ).stdout.strip().splitlines()
    dates: dict[str, str] = {}
    for line in log:
        commit, date = line.split("\t")
        diff = subprocess.run(
            ["git", "-C", str(repo), "show", commit, "--", "CHANGELOG.md"],
            check=True, capture_output=True, text=True,
        ).stdout
        for added in re.findall(r"^\+##\s+v?(\d+\.\d+\.\d+\S*)\s*$", diff, re.M):
            dates.setdefault(added, date)
    return dates


def collect(repo_dir: Path = Path("data/raw/claude-code"),
            out: Path = Path("data/processed/changelog.parquet")) -> Path:
    """End-to-end: clone repo, parse, date, write Parquet."""
    import polars as pl

    repo = clone_or_update_repo(repo_dir)
    entries = parse_changelog((repo / "CHANGELOG.md").read_text())
    dates = version_dates(repo)
    undated = sorted({e["version"] for e in entries} - set(dates))
    if undated:
        print(f"WARNING: {len(undated)} versions have no git date: {undated}")
    for e in entries:
        e["date"] = dates.get(e["version"])
    df = pl.DataFrame(entries)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.write_parquet(out)
    print(f"Wrote {len(df)} changelog entries to {out}")
    return out


if __name__ == "__main__":
    collect()
