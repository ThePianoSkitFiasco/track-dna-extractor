"""Launch the Track DNA Extractor desktop app."""

from __future__ import annotations

def main() -> None:
    """Start the Tkinter application."""
    from track_dna.ui.main_window import MainWindow

    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
