# Analysis Package

This package contains the framework-independent Python analysis engine. It remains callable without
FastAPI, a frontend, a database, or an external AI service.

The implemented Mixing v1 surface is:

```python
from secondear_analysis import analyze_mixing

result = analyze_mixing(
    "master.wav",
    "rap",
    reference_path="reference.flac",
)
```

The engine accepts stereo WAV/FLAC audio at 44.1 kHz or above with a duration of 30--600 seconds.
Demucs `htdemucs_ft` estimates `vocals`, `drums`, `bass`, and `other` for element-balance
measurements; the final score is produced only by the open formula and a released, version-matched
genre profile.

Install with Python 3.12:

```bash
pip install -e '.[dev,separation]'
pytest -q
secondear-mixing analyze master.wav --genre pop --profiles profiles/mixing --pretty
```

See `docs/MIXING.md` for the result contract, formula, corpus rules, CLI workflow, conformance setup,
and current limitations.
