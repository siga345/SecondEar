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

## English Rhymes 0.1

The Rhymes slice is text-only and has no network, database, FastAPI, frontend, or external-AI
dependency. It accepts line-broken lyrics, `en-US` or `en-GB`, one of six primary tags, and optional
occurrence-level pronunciation overrides. The result includes applicability, score when applicable,
independent confidence, pronunciation issues, evidence spans, relationships, complete-link families,
schemes, metrics, findings, limitations, and behavior-changing versions.

```python
from secondear_analysis import (
    LanguageProfile,
    PrimaryTag,
    RhymeAnalysisRequest,
    analyze_rhymes,
)

result = analyze_rhymes(
    RhymeAnalysisRequest(
        lyrics="Night arrives beneath the light\nWe write until the morning bright",
        language_profile=LanguageProfile.EN_US,
        primary_tag=PrimaryTag.POP,
    )
)
```

The package parses pinned official CMUdict data directly for `en-US` and pinned Britfone 3.0.1 data
for the Standard Southern British/RP `en-GB` profile. It never substitutes the US dictionary for a
missing UK entry.
