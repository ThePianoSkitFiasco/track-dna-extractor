"""File and export path helpers."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def safe_slug(text: str) -> str:
    """Convert arbitrary text into a filesystem-friendly slug."""
    stripped = text.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", stripped)
    collapsed = normalized.strip("-")
    return collapsed or "untitled"


def timestamp_string() -> str:
    """Return a compact local timestamp suitable for filenames."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def ensure_unique_path(path: str | Path) -> Path:
    """Return a unique path by appending a counter if needed."""
    candidate = Path(path)
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    parent = candidate.parent
    counter = 1

    while True:
        alternative = parent / f"{stem}-{counter}{suffix}"
        if not alternative.exists():
            return alternative
        counter += 1


def make_export_basename(source_audio_path: str | Path) -> str:
    """Build a descriptive export basename from the source audio filename."""
    source_path = Path(source_audio_path)
    name_slug = safe_slug(source_path.stem)
    return f"{name_slug}-{timestamp_string()}"
