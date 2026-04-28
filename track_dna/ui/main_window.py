"""Tkinter UI for the Track DNA Extractor v1 workflow."""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path
from dataclasses import replace

from track_dna.analyzers.basic_audio_analyzer import BasicAudioAnalyzer
from track_dna.models.analysis_result import AnalysisResult
from track_dna.prompts.prompt_builder import PromptBuilder
from track_dna.reports.report_writer import EXPORTS_DIR, export_reports
from track_dna.reports.report_templates import format_list_items
from track_dna.utils.time_utils import seconds_to_mmss

TKINTER_IMPORT_ERROR: Exception | None = None

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from tkinter.scrolledtext import ScrolledText
except Exception as exc:  # pragma: no cover - environment-specific dependency path
    tk = None
    filedialog = None
    messagebox = None
    ttk = None
    ScrolledText = None
    TKINTER_IMPORT_ERROR = exc


if tk is None:

    class MainWindow:
        """Fallback class when Tkinter is not available."""

        def __init__(self) -> None:
            raise RuntimeError(
                "Tkinter is not available in this Python environment. "
                "Install a Python build with Tk support to launch the desktop app."
            ) from TKINTER_IMPORT_ERROR

else:

    class MainWindow(tk.Tk):
        """Main desktop window for the Track DNA Extractor app."""

        def __init__(self) -> None:
            super().__init__()
            self.title("Track DNA Extractor")
            self.geometry("1100x820")
            self.minsize(900, 700)

            self.analyzer = BasicAudioAnalyzer()
            self.prompt_builder = PromptBuilder()
            self.current_result: AnalysisResult | None = None
            self.selected_file: Path | None = None

            self.status_var = tk.StringVar(value="Ready")
            self.selected_file_var = tk.StringVar(value="No audio file selected yet.")

            self._configure_theme()
            self._build_layout()
            self._update_button_states()

        def _configure_theme(self) -> None:
            """Apply a simple dark-ish theme with readable controls."""
            self.configure(bg="#15181d")
            style = ttk.Style(self)
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass

            style.configure("App.TFrame", background="#15181d")
            style.configure("Card.TFrame", background="#1d222a")
            style.configure("Title.TLabel", background="#15181d", foreground="#f2f4f8", font=("Helvetica", 18, "bold"))
            style.configure("Body.TLabel", background="#15181d", foreground="#d7dde7", font=("Helvetica", 11))
            style.configure("Muted.TLabel", background="#15181d", foreground="#9da8b8", font=("Helvetica", 10))
            style.configure("Status.TLabel", background="#15181d", foreground="#d7dde7", font=("Helvetica", 10, "bold"))
            style.configure("App.TButton", font=("Helvetica", 11, "bold"), padding=(14, 10))
            style.configure("App.TNotebook", background="#15181d", borderwidth=0)
            style.configure("App.TNotebook.Tab", font=("Helvetica", 10, "bold"), padding=(12, 8))

        def _build_layout(self) -> None:
            """Build the main window layout."""
            root = ttk.Frame(self, style="App.TFrame", padding=18)
            root.pack(fill="both", expand=True)
            root.columnconfigure(0, weight=1)
            root.rowconfigure(2, weight=1)

            header = ttk.Frame(root, style="App.TFrame")
            header.grid(row=0, column=0, sticky="ew")
            header.columnconfigure(0, weight=1)

            ttk.Label(header, text="Track DNA Extractor", style="Title.TLabel").grid(
                row=0, column=0, sticky="w"
            )
            ttk.Label(
                header,
                text="Choose a song file. The app will estimate its musical DNA and create reimagining prompts for Udio/Suno.",
                style="Body.TLabel",
                wraplength=960,
                justify="left",
            ).grid(row=1, column=0, sticky="w", pady=(6, 0))

            controls = ttk.Frame(root, style="Card.TFrame", padding=16)
            controls.grid(row=1, column=0, sticky="ew", pady=(16, 16))
            controls.columnconfigure(1, weight=1)
            controls.columnconfigure(2, weight=0)

            self.choose_button = ttk.Button(
                controls,
                text="Choose Audio File",
                style="App.TButton",
                command=self._choose_audio_file,
            )
            self.choose_button.grid(row=0, column=0, sticky="w")

            ttk.Label(
                controls,
                textvariable=self.selected_file_var,
                style="Body.TLabel",
                wraplength=700,
                justify="left",
            ).grid(row=0, column=1, sticky="w", padx=(14, 0))

            self.analyse_button = ttk.Button(
                controls,
                text="Analyse Track",
                style="App.TButton",
                command=self._analyse_track,
            )
            self.analyse_button.grid(row=0, column=2, sticky="e", padx=(12, 0))

            ttk.Label(
                controls,
                text="Optional notes: style references, mood, voice, what to avoid",
                style="Body.TLabel",
            ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(16, 4))

            ttk.Label(
                controls,
                text="Example: Jamie T meets London Grammar, sad but euphoric chorus, avoid EDM",
                style="Muted.TLabel",
                wraplength=920,
                justify="left",
            ).grid(row=2, column=0, columnspan=3, sticky="w")

            self.user_notes_text = ScrolledText(
                controls,
                height=5,
                wrap="word",
                font=("Helvetica", 11),
                bg="#0f1318",
                fg="#f2f4f8",
                insertbackground="#f2f4f8",
                relief="flat",
                padx=12,
                pady=12,
            )
            self.user_notes_text.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(8, 12))

            ttk.Label(
                controls,
                text="Optional AI/music description: paste a detailed description from MOSS-Audio or another tool",
                style="Body.TLabel",
            ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(4, 4))

            self.ai_description_text = ScrolledText(
                controls,
                height=6,
                wrap="word",
                font=("Helvetica", 11),
                bg="#0f1318",
                fg="#f2f4f8",
                insertbackground="#f2f4f8",
                relief="flat",
                padx=12,
                pady=12,
            )
            self.ai_description_text.grid(
                row=5,
                column=0,
                columnspan=3,
                sticky="ew",
                pady=(8, 12),
            )

            actions = ttk.Frame(controls, style="Card.TFrame")
            actions.grid(row=6, column=0, columnspan=3, sticky="ew")

            self.export_button = ttk.Button(
                actions,
                text="Export TXT + JSON",
                style="App.TButton",
                command=self._export_reports,
            )
            self.export_button.grid(row=0, column=0, sticky="w")

            self.open_exports_button = ttk.Button(
                actions,
                text="Open Exports Folder",
                style="App.TButton",
                command=self._open_exports_folder,
            )
            self.open_exports_button.grid(row=0, column=1, sticky="w", padx=(12, 0))

            notebook = ttk.Notebook(root, style="App.TNotebook")
            notebook.grid(row=2, column=0, sticky="nsew")

            self.result_panels: dict[str, ScrolledText] = {}
            tab_specs = [
                ("Summary", "summary"),
                ("Musical DNA", "dna"),
                ("Structure", "structure"),
                ("Udio Prompt", "udio"),
                ("Suno Prompt", "suno"),
                ("Negative Prompt", "negative"),
                ("Confidence Notes", "confidence"),
            ]
            for tab_label, key in tab_specs:
                frame = ttk.Frame(notebook, style="Card.TFrame", padding=10)
                frame.columnconfigure(0, weight=1)
                frame.rowconfigure(0, weight=1)
                text_widget = ScrolledText(
                    frame,
                    wrap="word",
                    font=("Helvetica", 11),
                    bg="#0f1318",
                    fg="#f2f4f8",
                    insertbackground="#f2f4f8",
                    relief="flat",
                    padx=12,
                    pady=12,
                )
                text_widget.grid(row=0, column=0, sticky="nsew")
                notebook.add(frame, text=tab_label)
                self.result_panels[key] = text_widget

            status_bar = ttk.Frame(root, style="App.TFrame")
            status_bar.grid(row=3, column=0, sticky="ew", pady=(12, 0))
            ttk.Label(status_bar, textvariable=self.status_var, style="Status.TLabel").grid(
                row=0, column=0, sticky="w"
            )

            self._fill_initial_results()

        def _fill_initial_results(self) -> None:
            """Set default text in all result panels."""
            default_text = "Results will appear here after you analyse a track."
            for widget in self.result_panels.values():
                self._set_text(widget, default_text)

        def _choose_audio_file(self) -> None:
            """Open a file picker for the source audio file."""
            file_path = filedialog.askopenfilename(
                title="Choose an audio file",
                filetypes=[
                    ("Audio files", "*.wav *.mp3 *.flac *.ogg *.m4a *.aiff *.aif"),
                    ("All files", "*.*"),
                ],
            )
            if not file_path:
                return

            self.selected_file = Path(file_path)
            self.selected_file_var.set(str(self.selected_file))
            self.status_var.set("Ready")
            self.current_result = None
            self._fill_initial_results()
            self._update_button_states()

        def _analyse_track(self) -> None:
            """Run the analysis and prompt generation flow."""
            if self.selected_file is None:
                self.status_var.set("Problem: Choose an audio file first.")
                return

            self.status_var.set("Analysing...")
            self.update_idletasks()

            user_notes = self.user_notes_text.get("1.0", "end").strip()
            ai_description = self.ai_description_text.get("1.0", "end").strip()
            try:
                base_result = self.analyzer.analyze_file(
                    str(self.selected_file),
                    user_notes=user_notes,
                )
                if ai_description:
                    base_result = replace(
                        base_result,
                        ai_description_notes=[ai_description],
                    )
                final_result = self.prompt_builder.enrich_result(
                    base_result,
                    user_notes=user_notes,
                    ai_description_notes=ai_description,
                )
            except Exception as exc:
                friendly_message = str(exc).strip() or "Unknown problem during analysis."
                self.current_result = None
                self._update_button_states()
                self.status_var.set(f"Problem: {friendly_message}")
                messagebox.showerror("Track DNA Extractor", friendly_message)
                return

            self.current_result = final_result
            self._populate_results(final_result)
            self._update_button_states()
            self.status_var.set("Done")

        def _populate_results(self, result: AnalysisResult) -> None:
            """Render the result into the tab panels."""
            self._set_text(self.result_panels["summary"], result.summary or "No summary available.")
            self._set_text(self.result_panels["dna"], self._build_dna_text(result))
            self._set_text(self.result_panels["structure"], self._build_structure_text(result))
            self._set_text(self.result_panels["udio"], result.udio_prompt or "No Udio prompt generated.")
            self._set_text(self.result_panels["suno"], result.suno_prompt or "No Suno prompt generated.")
            self._set_text(self.result_panels["negative"], result.negative_prompt or "No negative prompt generated.")
            self._set_text(
                self.result_panels["confidence"],
                format_list_items(
                    result.confidence_notes,
                    empty_text="No confidence notes available.",
                ),
            )

        def _build_dna_text(self, result: AnalysisResult) -> str:
            """Create a readable Musical DNA panel."""
            bpm_text = (
                f"{round(result.estimated_bpm, 1)} BPM"
                if result.estimated_bpm is not None
                else "No reliable BPM estimate"
            )
            parts = [
                f"Source file: {result.source_file}",
                f"Duration: {seconds_to_mmss(result.duration_seconds)}",
                f"Tempo estimate: {bpm_text}",
                f"Loudness feel: {result.loudness_description or 'Not available'}",
                f"Energy feel: {result.energy_description or 'Not available'}",
                f"Brightness feel: {result.brightness_description or 'Not available'}",
                f"Rhythm feel: {result.rhythm_description or 'Not available'}",
                f"Vocal read: {result.vocal_description or 'Not available'}",
                "",
                "User Notes",
                format_list_items(result.user_notes, empty_text="No user notes provided."),
                "",
                "Optional AI / Music Description",
                format_list_items(
                    result.ai_description_notes,
                    empty_text="No pasted AI or external audio description provided.",
                ),
                "",
                "Genre / Style Notes",
                format_list_items(result.genre_style_notes),
                "",
                "Mood Notes",
                format_list_items(result.mood_notes),
                "",
                "Instrumentation Notes",
                format_list_items(result.instrumentation_notes),
                "",
                "Production Notes",
                format_list_items(result.production_notes),
                "",
                "Standout Moments",
                format_list_items(result.standout_moments),
            ]
            return "\n".join(parts)

        def _build_structure_text(self, result: AnalysisResult) -> str:
            """Create a readable structure panel."""
            if not result.structure_sections:
                return "No structure estimate available."

            lines = []
            for section in result.structure_sections:
                lines.append(
                    f"{section.label}\n"
                    f"{seconds_to_mmss(section.start_seconds)} - {seconds_to_mmss(section.end_seconds)}\n"
                    f"{section.description}\n"
                    f"Confidence: {section.confidence:.2f}\n"
                )
            return "\n".join(lines).strip()

        def _export_reports(self) -> None:
            """Write TXT and JSON report files for the current analysis."""
            if self.current_result is None:
                self.status_var.set("Problem: Analyse a track before exporting.")
                return

            try:
                paths = export_reports(self.current_result)
            except Exception as exc:
                friendly_message = str(exc).strip() or "Could not export report files."
                self.status_var.set(f"Problem: {friendly_message}")
                messagebox.showerror("Track DNA Extractor", friendly_message)
                return

            message = (
                f"Saved TXT report:\n{paths['txt'].resolve()}\n\n"
                f"Saved JSON report:\n{paths['json'].resolve()}"
            )
            self.status_var.set("Done")
            messagebox.showinfo("Track DNA Extractor", message)

        def _open_exports_folder(self) -> None:
            """Open the exports folder in the platform file manager if possible."""
            export_path = EXPORTS_DIR.resolve()
            export_path.mkdir(parents=True, exist_ok=True)

            try:
                system_name = platform.system()
                if system_name == "Darwin":
                    subprocess.run(["open", str(export_path)], check=True)
                elif system_name == "Windows":
                    subprocess.run(["explorer", str(export_path)], check=True)
                else:
                    subprocess.run(["xdg-open", str(export_path)], check=True)
            except Exception:
                messagebox.showinfo(
                    "Track DNA Extractor",
                    f"Exports folder:\n{export_path}",
                )

        def _set_text(self, widget: ScrolledText, text: str) -> None:
            """Replace text in a panel while keeping it editable for copy/paste."""
            widget.delete("1.0", "end")
            widget.insert("1.0", text)

        def _update_button_states(self) -> None:
            """Enable or disable buttons based on current app state."""
            self.analyse_button.state(
                ["!disabled"] if self.selected_file is not None else ["disabled"]
            )
            self.export_button.state(
                ["!disabled"] if self.current_result is not None else ["disabled"]
            )
