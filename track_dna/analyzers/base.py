"""Shared analyzer contract for local audio backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from track_dna.models.analysis_result import AnalysisResult


class BaseAnalyzer(ABC):
    """Minimal interface for any analyzer backend."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the human-readable analyzer name."""

    @abstractmethod
    def analyze_file(self, audio_path: str, user_notes: str = "") -> AnalysisResult:
        """Analyze one local audio file and return a normalized result."""
