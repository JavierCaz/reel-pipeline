"""Shared plumbing for the reel pipeline: project paths, config, JSON I/O, word lookup."""

from __future__ import annotations

import json
import math
import re
import shutil
import unicodedata
from pathlib import Path

PROJECT: Path = Path.cwd()
CONFIG: dict = {}
FPS = 30


def load(project: Path) -> dict:
    """Read <project>/reel.config.json and remember the project root for every step."""
    global PROJECT, CONFIG, FPS
    PROJECT = project.resolve()
    path = PROJECT / "reel.config.json"
    if not path.exists():
        raise SystemExit(f"No reel.config.json in {PROJECT}. Copy it from _templates/short-template/.")
    CONFIG = json.loads(path.read_text())
    FPS = CONFIG.get("fps", 30)
    for key in ("id", "visual_prefix"):
        if not CONFIG.get(key):
            raise SystemExit(f"reel.config.json needs '{key}'")
    return CONFIG


def p(relative: str) -> Path:
    return PROJECT / relative


def read_json(relative: str, default=None):
    path = p(relative)
    if not path.exists():
        if default is not None:
            return default
        raise SystemExit(f"Missing {relative}; run the step that produces it first.")
    return json.loads(path.read_text())


def write_json(relative: str, data) -> None:
    path = p(relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def npx() -> str:
    """The npx executable. On Windows it is npx.cmd, which subprocess does not find by the bare name."""
    found = shutil.which("npx")
    if not found:
        raise SystemExit("npx not found: install Node.js, then open a new terminal")
    return found


def hyperframes_pin() -> str:
    """The exact hyperframes@X.Y.Z pinned in the project's package.json scripts."""
    scripts = json.loads(p("package.json").read_text()).get("scripts", {})
    for command in scripts.values():
        match = re.search(r"hyperframes@(\d+\.\d+\.\d+)", command)
        if match:
            return f"hyperframes@{match.group(1)}"
    raise SystemExit("package.json must pin an exact hyperframes@X.Y.Z")


def frame_floor(seconds: float) -> int:
    return int(seconds * FPS + 1e-7)


def frame_ceil(seconds: float) -> int:
    return math.ceil(seconds * FPS - 1e-7)


def norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "", text)


def make_T(words: list[dict]):
    """Return T(phrase, after=0): start time of the first spoken occurrence at or after `after`."""
    normed = [norm(w["text"]) for w in words]

    def T(phrase: str, after: float = 0) -> float:
        query = [norm(x) for x in phrase.split()]
        for i, word in enumerate(words):
            if word["start"] >= after and normed[i:i + len(query)] == query:
                return round(word["start"], 3)
        raise ValueError(f"phrase not found: {phrase!r} after {after}")

    return T
