"""Basic local audio analyzer using common Python audio libraries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from track_dna.analyzers.base import BaseAnalyzer
from track_dna.models.analysis_result import AnalysisResult, StructureSection
from track_dna.utils.time_utils import seconds_range_to_label

_DEPENDENCY_ERROR: Exception | None = None

try:
    import librosa
    import numpy as np
    import soundfile as sf
except Exception as exc:  # pragma: no cover - exercised in dependency failure paths
    librosa = None
    np = None
    sf = None
    _DEPENDENCY_ERROR = exc


class BasicAudioAnalyzer(BaseAnalyzer):
    """A simple analyzer that extracts broad signal-based traits."""

    @property
    def name(self) -> str:
        return "Basic Local Audio Analyzer"

    def analyze_file(self, audio_path: str, user_notes: str = "") -> AnalysisResult:
        """Analyze a local audio file using lightweight signal features."""
        source_path = Path(audio_path).expanduser()
        if not source_path.exists():
            raise FileNotFoundError(f"Audio file not found: {source_path}")

        self._ensure_dependencies()

        try:
            file_info = sf.info(str(source_path))
        except Exception as exc:
            raise RuntimeError(
                f"Could not read audio file metadata for '{source_path.name}'."
            ) from exc

        try:
            audio, sample_rate = librosa.load(
                str(source_path),
                sr=None,
                mono=True,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Could not load audio file '{source_path.name}'. "
                "Make sure it is a supported local audio format and that the "
                "required audio dependencies are installed."
            ) from exc

        if audio.size == 0:
            raise RuntimeError(f"Audio file '{source_path.name}' appears to be empty.")

        duration_seconds = float(librosa.get_duration(y=audio, sr=sample_rate))
        channels = int(getattr(file_info, "channels", 0) or 0)

        rms = librosa.feature.rms(y=audio)[0]
        rms_mean = float(np.mean(rms))
        rms_max = float(np.max(rms))

        spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sample_rate)[0]
        spectral_centroid_mean = float(np.mean(spectral_centroid))

        onset_frames = librosa.onset.onset_detect(y=audio, sr=sample_rate)
        onset_count = int(len(onset_frames))
        onset_density = float(onset_count / duration_seconds) if duration_seconds > 0 else 0.0

        tempo: float | None = None
        tempo_confidence_note = ""
        try:
            tempo_array = librosa.beat.tempo(y=audio, sr=sample_rate)
            if len(tempo_array) > 0:
                tempo = float(tempo_array[0])
        except Exception:
            tempo_confidence_note = (
                "Tempo could not be estimated reliably from the basic signal analysis."
            )

        structure_sections = self._build_structure_sections(audio, sample_rate, duration_seconds)
        standout_moments = self._build_standout_moments(audio, sample_rate, duration_seconds)
        user_notes_list = [user_notes.strip()] if user_notes.strip() else []

        confidence_notes = [
            "This v1 analyzer uses basic signal analysis only, not deep musical understanding.",
            "Section labels and descriptive traits are approximate best guesses.",
            "Vocals, lyrics, exact genre, and instrumentation are not deeply analysed in v1.",
        ]
        if tempo_confidence_note:
            confidence_notes.append(tempo_confidence_note)
        elif tempo is None:
            confidence_notes.append(
                "Tempo estimate is unavailable for this file from the current v1 analysis."
            )

        return AnalysisResult(
            source_file=str(source_path),
            duration_seconds=duration_seconds,
            sample_rate=int(sample_rate),
            channels=channels,
            estimated_bpm=round(tempo, 1) if tempo is not None else None,
            loudness_description=self._describe_loudness(rms_mean, rms_max),
            energy_description=self._describe_energy(rms_mean, onset_density),
            brightness_description=self._describe_brightness(spectral_centroid_mean),
            rhythm_description=self._describe_rhythm(onset_density, tempo),
            likely_vocals="unknown",
            vocal_description="Not analysed in v1.",
            genre_style_notes=["Not analysed in v1."],
            mood_notes=[],
            instrumentation_notes=["Not analysed in v1."],
            production_notes=self._build_production_notes(
                rms_mean=rms_mean,
                rms_max=rms_max,
                spectral_centroid_mean=spectral_centroid_mean,
                onset_density=onset_density,
            ),
            structure_sections=structure_sections,
            standout_moments=standout_moments,
            user_notes=user_notes_list,
            confidence_notes=confidence_notes,
            raw_features={
                "rms_mean": round(rms_mean, 6),
                "rms_max": round(rms_max, 6),
                "spectral_centroid_mean": round(spectral_centroid_mean, 3),
                "onset_count": onset_count,
                "onset_density": round(onset_density, 4),
                "tempo": round(tempo, 3) if tempo is not None else None,
                "duration_seconds": round(duration_seconds, 3),
            },
        )

    def _ensure_dependencies(self) -> None:
        """Raise a friendly error if required audio libraries are unavailable."""
        if _DEPENDENCY_ERROR is None:
            return
        raise RuntimeError(
            "BasicAudioAnalyzer requires local audio dependencies: librosa, "
            "soundfile, and numpy. Install the packages in requirements.txt "
            "before analyzing audio files."
        ) from _DEPENDENCY_ERROR

    def _describe_loudness(self, rms_mean: float, rms_max: float) -> str:
        """Map RMS values to a readable loudness description."""
        loudness_score = (rms_mean * 0.7) + (rms_max * 0.3)
        if loudness_score < 0.04:
            return "quiet"
        if loudness_score < 0.09:
            return "moderate"
        if loudness_score < 0.16:
            return "loud"
        return "very loud"

    def _describe_energy(self, rms_mean: float, onset_density: float) -> str:
        """Map broad intensity features to a simple energy label."""
        energy_score = (rms_mean * 3.0) + (onset_density * 0.15)
        if energy_score < 0.25:
            return "sparse and restrained"
        if energy_score < 0.55:
            return "balanced"
        return "dense and energetic"

    def _describe_brightness(self, spectral_centroid_mean: float) -> str:
        """Map spectral centroid to a readable tonal balance description."""
        if spectral_centroid_mean < 1500:
            return "dark and warm"
        if spectral_centroid_mean < 3000:
            return "balanced"
        return "bright and sharp"

    def _describe_rhythm(self, onset_density: float, tempo: float | None) -> str:
        """Describe how active the rhythm feels from a basic onset estimate."""
        if onset_density < 0.8:
            return "very sparse rhythm"
        if onset_density < 2.5:
            return "steady pulse"
        if tempo is not None and tempo >= 140 and onset_density >= 3.0:
            return "fast and busy rhythmic movement"
        return "busy rhythmic movement"

    def _build_production_notes(
        self,
        rms_mean: float,
        rms_max: float,
        spectral_centroid_mean: float,
        onset_density: float,
    ) -> list[str]:
        """Build simple production notes from the analyzer's existing estimates."""
        loudness_description = self._describe_loudness(rms_mean, rms_max)
        energy_description = self._describe_energy(rms_mean, onset_density)
        brightness_description = self._describe_brightness(spectral_centroid_mean)
        rhythm_description = self._describe_rhythm(onset_density, tempo=None)

        notes = [
            f"{loudness_description.capitalize()} loudness with {energy_description} energy.",
            f"{brightness_description.capitalize()} tonal balance suggested by the brightness estimate.",
            f"Rhythm feel: {rhythm_description}.",
        ]

        cleaned_notes = [note.strip() for note in notes if note.strip()]
        if cleaned_notes:
            return cleaned_notes
        return ["Production traits are estimated from basic signal analysis only."]

    def _build_structure_sections(
        self,
        audio: Any,
        sample_rate: int,
        duration_seconds: float,
    ) -> list[StructureSection]:
        """Create safe approximate sections based on duration and energy changes."""
        if duration_seconds <= 0:
            return []

        if duration_seconds < 45:
            split_points = [0.0, duration_seconds * 0.35, duration_seconds]
            labels = ["Approx. intro", "Approx. main section"]
        elif duration_seconds < 120:
            split_points = [
                0.0,
                duration_seconds * 0.2,
                duration_seconds * 0.75,
                duration_seconds,
            ]
            labels = ["Approx. intro", "Approx. main section", "Approx. later section / outro"]
        else:
            split_points = [
                0.0,
                duration_seconds * 0.15,
                duration_seconds * 0.55,
                duration_seconds * 0.85,
                duration_seconds,
            ]
            labels = [
                "Approx. intro",
                "Approx. main section",
                "Approx. later section",
                "Approx. outro",
            ]

        sections: list[StructureSection] = []
        rms = librosa.feature.rms(y=audio)[0]
        frame_times = librosa.times_like(rms, sr=sample_rate)

        for index, label in enumerate(labels):
            start = float(split_points[index])
            end = float(split_points[index + 1])
            energy_hint = self._section_energy_hint(rms, frame_times, start, end)
            sections.append(
                StructureSection(
                    label=label,
                    start_seconds=round(start, 2),
                    end_seconds=round(end, 2),
                    description=f"Approximate section from {seconds_range_to_label(start, end)}. {energy_hint}",
                    confidence=0.35,
                )
            )

        return sections

    def _section_energy_hint(
        self,
        rms: Any,
        frame_times: Any,
        start_seconds: float,
        end_seconds: float,
    ) -> str:
        """Summarize whether a section feels lower or higher in energy."""
        mask = (frame_times >= start_seconds) & (frame_times < end_seconds)
        if not np.any(mask):
            return "Energy profile is unclear."

        section_mean = float(np.mean(rms[mask]))
        if section_mean < 0.04:
            return "Feels relatively restrained."
        if section_mean < 0.09:
            return "Feels moderately active."
        return "Feels more intense and forward."

    def _build_standout_moments(
        self,
        audio: Any,
        sample_rate: int,
        duration_seconds: float,
    ) -> list[str]:
        """Find rough high-energy windows that may stand out."""
        rms = librosa.feature.rms(y=audio)[0]
        if len(rms) == 0:
            return []

        frame_times = librosa.times_like(rms, sr=sample_rate)
        threshold = float(np.mean(rms) + np.std(rms))
        candidate_indices = np.where(rms >= threshold)[0]
        if len(candidate_indices) == 0:
            return []

        standout_times: list[float] = []
        last_time = -999.0
        minimum_gap = max(8.0, duration_seconds * 0.08)

        for index in candidate_indices:
            time_value = float(frame_times[index])
            if time_value - last_time >= minimum_gap:
                standout_times.append(time_value)
                last_time = time_value
            if len(standout_times) >= 3:
                break

        return [
            f"Possible standout moment near {seconds_range_to_label(time_value, min(time_value + 8.0, duration_seconds))}"
            for time_value in standout_times
        ]
