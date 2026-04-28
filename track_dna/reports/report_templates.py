"""Small formatting helpers for user-facing reports."""

from __future__ import annotations


def format_list_items(items: list[str], empty_text: str = "None noted.") -> str:
    """Format a list as one item per line for text reports."""
    cleaned = [item.strip() for item in items if item and item.strip()]
    if not cleaned:
        return f"- {empty_text}"
    return "\n".join(f"- {item}" for item in cleaned)
