"""Reads the copyable prompt text out of a prompt file. See PROMPT-DESIGN.md for the file contract."""

import hashlib
from pathlib import Path

HEADING = "## The prompt"


def read_prompt(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    i = text.find(HEADING)
    if i == -1:
        raise ValueError(f"{path} has no '{HEADING}' heading")
    return text[i + len(HEADING):].strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
