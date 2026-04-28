"""Report export helpers for Track DNA Extractor."""

from __future__ import annotations

import json
from pathlib import Path

from track_dna.models.analysis_result import AnalysisResult
from track_dna.reports.report_templates import format_list_items
from track_dna.utils.file_utils import ensure_unique_path, make_export_basename
from track_dna.utils.time_utils import seconds_to_mmss

EXPORTS_DIR = Path("exports")


def export_reports(
    result: AnalysisResult,
    export_dir: str | Path = EXPORTS_DIR,
) -> dict[str, Path]:
    """Export both TXT and JSON reports and return their paths."""
    base_name = make_export_basename(result.source_file)
    export_path = Path(export_dir)
    export_path.mkdir(parents=True, exist_ok=True)

    txt_path = ensure_unique_path(export_path / f"{base_name}.txt")
    json_path = ensure_unique_path(export_path / f"{base_name}.json")

    txt_path.write_text(build_txt_report(result), encoding="utf-8")
    json_path.write_text(
        json.dumps(result.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {"txt": txt_path, "json": json_path}


def build_txt_report(result: AnalysisResult) -> str:
    """Build a readable plain-text report."""
    bpm_text = (
        f"{round(result.estimated_bpm, 1)} BPM"
        if result.estimated_bpm is not None
        else "No reliable BPM estimate"
    )
    structure_text = _format_structure(result)
    return "\n".join(
        [
            "Track DNA Report",
            "",
            f"Source file: {result.source_file}",
            f"Analysed at: {result.analysed_at}",
            f"Duration: {seconds_to_mmss(result.duration_seconds)}",
            f"BPM estimate: {bpm_text}",
            "",
            "User Notes",
            format_list_items(result.user_notes, empty_text="No user notes provided."),
            "",
            "Plain-English Summary",
            result.summary or "Summary not generated yet.",
            "",
            "Musical DNA",
            f"- Loudness feel: {result.loudness_description or 'Not available'}",
            f"- Energy feel: {result.energy_description or 'Not available'}",
            f"- Brightness feel: {result.brightness_description or 'Not available'}",
            f"- Rhythm feel: {result.rhythm_description or 'Not available'}",
            f"- Vocal read: {result.vocal_description or 'Not available'}",
            _optional_block("Genre / Style Notes", result.genre_style_notes),
            _optional_block("Mood Notes", result.mood_notes),
            _optional_block("Instrumentation Notes", result.instrumentation_notes),
            _optional_block("Production Notes", result.production_notes),
            "",
            "Approximate Structure",
            structure_text,
            "",
            "Standout Moments",
            format_list_items(result.standout_moments),
            "",
            "Udio Prompt",
            result.udio_prompt or "Not generated yet.",
            "",
            "Suno Prompt",
            result.suno_prompt or "Not generated yet.",
            "",
            "Negative Prompt",
            result.negative_prompt or "Not generated yet.",
            "",
            "Confidence Notes",
            format_list_items(result.confidence_notes),
            "",
            "V1 Limitations",
            "This version uses basic local signal analysis only. Treat the report as an approximate creative guide, not a precise reconstruction of the source track.",
        ]
    )


def _optional_block(title: str, items: list[str]) -> str:
    """Build a compact titled block for report sections."""
    return f"{title}:\n{format_list_items(items)}"


def _format_structure(result: AnalysisResult) -> str:
    """Format structure sections for a text report."""
    if not result.structure_sections:
        return "- No structure estimate available."

    lines = []
    for section in result.structure_sections:
        lines.append(
            f"- {section.label}: {seconds_to_mmss(section.start_seconds)}-{seconds_to_mmss(section.end_seconds)} | {section.description} | confidence {section.confidence:.2f}"
        )
    return "\n".join(lines)
