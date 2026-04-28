"""Helpers for formatting timestamps for readable reports."""

from __future__ import annotations


def seconds_to_mmss(seconds: float) -> str:
    """Format seconds as MM:SS using rounded whole seconds."""
    total_seconds = max(0, int(round(seconds)))
    minutes, remaining_seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"


def seconds_range_to_label(start: float, end: float) -> str:
    """Format a start and end time as a readable timestamp range."""
    return f"{seconds_to_mmss(start)}-{seconds_to_mmss(end)}"
