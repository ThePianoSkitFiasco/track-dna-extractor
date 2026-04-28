# Track DNA Extractor

Local-first macOS-friendly tool for analyzing a song's musical DNA and generating reimagining prompts.

This repository currently contains a simple Tkinter desktop app, a basic local audio analyzer, deterministic prompt generation, and report export helpers.

Basic local audio analysis depends on `librosa`, `soundfile`, and `numpy`. If those packages are missing, the analyzer raises a friendly runtime error instead of failing at import time.

Prompt generation and report export are fully local and deterministic. Reports can be exported as `.txt` and `.json` files into `exports/`.

Run the app locally with:

```bash
python app.py
```
