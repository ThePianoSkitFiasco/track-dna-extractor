"""Shared analysis result models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class StructureSection:
    """A best-effort section label with timestamp boundaries."""

    label: str
    start_seconds: float
    end_seconds: float
    description: str = ""
    confidence: float = 0.0


@dataclass
class AnalysisResult:
    """Normalized analysis output used by analyzers, reports, and prompts."""

    source_file: str
    analysed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    duration_seconds: float = 0.0
    sample_rate: int = 0
    channels: int = 0
    estimated_bpm: float | None = None
    loudness_description: str = ""
    energy_description: str = ""
    brightness_description: str = ""
    rhythm_description: str = ""
    summary: str = ""
    likely_vocals: bool | str | None = None
    vocal_description: str = ""
    genre_style_notes: list[str] = field(default_factory=list)
    mood_notes: list[str] = field(default_factory=list)
    instrumentation_notes: list[str] = field(default_factory=list)
    production_notes: list[str] = field(default_factory=list)
    structure_sections: list[StructureSection] = field(default_factory=list)
    standout_moments: list[str] = field(default_factory=list)
    user_notes: list[str] = field(default_factory=list)
    udio_prompt: str = ""
    suno_prompt: str = ""
    negative_prompt: str = ""
    confidence_notes: list[str] = field(default_factory=list)
    raw_features: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary representation."""
        return asdict(self)
