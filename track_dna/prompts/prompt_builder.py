"""Deterministic prompt and summary generation from analysis results."""

from __future__ import annotations

from dataclasses import replace

from track_dna.models.analysis_result import AnalysisResult


class PromptBuilder:
    """Build user-facing summaries and reimagining prompts."""

    def enrich_result(
        self, result: AnalysisResult, user_notes: str | list[str] | None = None
    ) -> AnalysisResult:
        """Return a copy of the result with summary and prompt fields populated."""
        notes = self._merge_user_notes(result.user_notes, user_notes)
        summary = self._build_summary(result, notes)
        udio_prompt = self._build_udio_prompt(result, notes)
        suno_prompt = self._build_suno_prompt(result, notes)
        negative_prompt = self._build_negative_prompt(result, notes)
        return replace(
            result,
            user_notes=notes,
            summary=summary,
            udio_prompt=udio_prompt,
            suno_prompt=suno_prompt,
            negative_prompt=negative_prompt,
        )

    def _merge_user_notes(
        self, existing_notes: list[str], incoming: str | list[str] | None
    ) -> list[str]:
        """Combine stored notes with optional extra notes without duplicates."""
        merged = [note.strip() for note in existing_notes if note.strip()]
        if isinstance(incoming, str):
            candidates = [incoming]
        else:
            candidates = incoming or []

        for note in candidates:
            cleaned = note.strip()
            if cleaned and cleaned not in merged:
                merged.append(cleaned)
        return merged

    def _build_summary(self, result: AnalysisResult, user_notes: list[str]) -> str:
        """Create a concise plain-English summary."""
        tempo_text = (
            f"around {round(result.estimated_bpm)} BPM"
            if result.estimated_bpm is not None
            else "with no reliable BPM estimate"
        )
        base = (
            f"This track reads as {result.energy_description or 'moderately energetic'}, "
            f"{result.brightness_description or 'tonally balanced'}, and "
            f"{result.rhythm_description or 'rhythmically steady'}, {tempo_text}. "
            f"It is best treated as a reimagining reference rather than something to clone exactly."
        )
        if user_notes:
            return f"{base} User direction suggests: {'; '.join(user_notes)}."
        return base

    def _build_udio_prompt(
        self, result: AnalysisResult, user_notes: list[str]
    ) -> str:
        """Create a detailed Udio-friendly prompt."""
        parts = [
            "Create an original song inspired by the musical DNA of this reference, but do not recreate it literally.",
            self._tempo_phrase(result),
            f"Aim for a {result.energy_description or 'balanced'} overall energy, "
            f"a {result.brightness_description or 'balanced'} tonal feel, and "
            f"{self._rhythm_clause(result)}.",
            self._optional_notes_phrase(
                "Style direction", result.genre_style_notes, fallback="best treated as stylistically open in v1"
            ),
            self._optional_notes_phrase(
                "Mood", result.mood_notes, fallback="suggesting a broad emotional shape rather than a fixed narrative"
            ),
            self._optional_notes_phrase(
                "Vocals", [result.vocal_description] if result.vocal_description else [],
                fallback="with a likely vocal approach still unknown from v1 analysis"
            ),
            self._optional_notes_phrase(
                "Instrumentation", result.instrumentation_notes,
                fallback="using instrumentation choices that fit the energy and mood"
            ),
            self._optional_notes_phrase(
                "Production", result.production_notes,
                fallback="with production choices guided by the broad loudness and brightness profile"
            ),
        ]
        if user_notes:
            parts.append(
                "Strongly prioritize these user notes when shaping the reimagining: "
                + "; ".join(user_notes)
                + "."
            )
        parts.append(
            "Keep the result original, emotionally coherent, and focused on the overall feel, pacing, and atmosphere rather than exact melody, lyrics, or arrangement."
        )
        return " ".join(part for part in parts if part)

    def _build_suno_prompt(
        self, result: AnalysisResult, user_notes: list[str]
    ) -> str:
        """Create a shorter Suno-friendly prompt."""
        parts = [
            "Original song inspired by this track's musical DNA, not a clone.",
            self._tempo_phrase(result),
            f"{self._capitalize(result.energy_description or 'balanced')} energy, "
            f"{result.brightness_description or 'balanced'} tone, "
            f"and {result.rhythm_description or 'steady rhythm'}.",
        ]
        short_notes = self._collect_short_notes(result, user_notes)
        if short_notes:
            parts.append("Focus on " + "; ".join(short_notes) + ".")
        parts.append("Aim for a clear hook and a convincing emotional arc.")
        return " ".join(parts)

    def _build_negative_prompt(
        self, result: AnalysisResult, user_notes: list[str]
    ) -> str:
        """Create a practical negative prompt."""
        negatives = [
            "do not clone the reference song",
            "avoid copying exact melody or lyrics",
            "avoid obvious imitation of arrangement details",
            "avoid generic preset-sounding production",
        ]
        if result.energy_description == "sparse and restrained":
            negatives.append("avoid overstuffing the arrangement")
        if result.brightness_description == "dark and warm":
            negatives.append("avoid harsh top-end")
        if result.brightness_description == "bright and sharp":
            negatives.append("avoid muddy low-mid build-up")
        for note in user_notes:
            negatives.extend(self._extract_negative_fragments(note))
        return ", ".join(dict.fromkeys(negatives))

    def _tempo_phrase(self, result: AnalysisResult) -> str:
        """Build a plain-English tempo phrase."""
        if result.estimated_bpm is None:
            return "Use a tempo that feels natural for the intended mood."
        rounded = round(result.estimated_bpm)
        return f"Use a tempo around {rounded} BPM."

    def _rhythm_clause(self, result: AnalysisResult) -> str:
        """Build a readable rhythm phrase."""
        rhythm = result.rhythm_description or "steady pulse"
        if rhythm.startswith("very") or rhythm.startswith("busy") or rhythm.startswith("fast"):
            return f"a {rhythm}"
        return f"a sense of {rhythm}"

    def _optional_notes_phrase(
        self, label: str, notes: list[str], fallback: str
    ) -> str:
        """Format a labeled note block with a fallback."""
        cleaned = [note.strip() for note in notes if note and note.strip()]
        if cleaned and cleaned != ["Not analysed in v1."]:
            return f"{label}: " + "; ".join(cleaned) + "."
        return f"{label}: {fallback}."

    def _collect_short_notes(
        self, result: AnalysisResult, user_notes: list[str]
    ) -> list[str]:
        """Gather short prompt fragments in priority order."""
        fragments: list[str] = []
        for bucket in (
            user_notes,
            result.mood_notes,
            result.genre_style_notes,
            result.instrumentation_notes,
            result.production_notes,
        ):
            for item in bucket:
                cleaned = item.strip()
                if cleaned and cleaned != "Not analysed in v1." and cleaned not in fragments:
                    fragments.append(cleaned)
                if len(fragments) >= 4:
                    return fragments
        return fragments

    def _extract_negative_fragments(self, note: str) -> list[str]:
        """Pull only explicit avoidance instructions from user notes."""
        fragments = []
        for part in note.replace(";", ",").split(","):
            cleaned = part.strip()
            lowered = cleaned.lower()
            if lowered.startswith("avoid "):
                fragments.append(cleaned)
            elif lowered.startswith("no "):
                fragments.append(cleaned)
            elif lowered.startswith("not "):
                fragments.append(cleaned)
        return fragments

    def _capitalize(self, text: str) -> str:
        """Capitalize the first character of a string safely."""
        if not text:
            return text
        return text[0].upper() + text[1:]
