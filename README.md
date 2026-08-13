# SecondEar

SecondEar is an open-source objective music analysis system for artists, producers, and engineers.
It uses digital signal processing, music information retrieval, and computational analysis to give
musicians an independent, evidence-based view of their own tracks.

> **No taste. No attachment. Just evidence.**

## Project status

SecondEar now contains the first framework-independent implementation of the Mixing criterion. It
accepts a lossless stereo master, extracts direct DSP and EBU R128 measurements, uses Demucs only as
a bounded stem estimator, and applies an inspectable genre-profile formula. The engine does not use
an LLM or an opaque score-prediction model.

The implemented Mixing v1 pipeline is:

```text
WAV/FLAC stereo master + primary genre + optional reference
  -> validation and full decoding
  -> loudness, dynamics, spectrum, stereo, and integrity measurements
  -> Demucs htdemucs_ft stem estimates for element-balance measurements
  -> versioned genre-profile penalties
  -> typed MixingResult
```

The repository also contains the complete English Rhymes 0.1 text slice:

```text
English lyrics
  -> normalized sections and source spans
  -> pinned en-US or en-GB pronunciation
  -> rhyme pairs, families, schemes, metrics, and findings
  -> genre-profile score with independent confidence
  -> synchronous FastAPI response
  -> accessible Next.js report
```

Rhymes analyzes only caller-supplied text. It does not transcribe audio, scrape lyrics, use an LLM,
or infer performed pronunciation. The deterministic 0.1 score uses published seed anchors that are
explicitly marked as awaiting private-corpus calibration and held-out validation.

No public Mixing profiles are bundled yet. Until a lawful 50-track corpus for a genre passes
calibration, validation, holdout, and conformance gates, the engine returns `insufficient_data`
instead of inventing a score. The complete contract is documented in
[docs/MIXING.md](docs/MIXING.md); the nine-criterion methodology is documented in
[docs/SCORING.md](docs/SCORING.md).

## Local development

Python 3.12 is required.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e '.[dev,separation]'
.venv/bin/python -m pytest -q
.venv/bin/secondear-mixing analyze track.wav --genre rap --pretty
```

The first Demucs run downloads the pinned `htdemucs_ft` weights. Run the opt-in real-model smoke
test with `SECONDEAR_RUN_DEMUCS=1`; see [docs/MIXING.md](docs/MIXING.md) for the EBU conformance
fixture setup and profile-building workflow.

## Repository map

```text
SecondEar/
├── apps/
│   ├── api/                 # FastAPI Rhymes transport layer
│   └── web/                 # Next.js Rhymes report
├── packages/
│   └── analysis/            # Framework-independent analysis engine
├── docs/
│   ├── PRODUCT.md
│   ├── ARCHITECTURE.md
│   ├── ANALYSIS_MODEL.md
│   ├── SCORING.md
│   ├── DECISIONS.md
│   └── ROADMAP.md
├── fixtures/                # Synthetic and redistributable test inputs
├── research-data/           # Gitignored local-corpus workflow
├── scripts/                 # Development and maintenance commands
├── tests/                   # Cross-package and end-to-end tests
└── AGENTS.md                # Durable project rules for coding agents
```

## Contributing

Start with [AGENTS.md](AGENTS.md), then read the documents in `docs/`. Analytical changes must preserve
the evidence chain, version formulas and profiles, and include deterministic synthetic tests. Do not
commit commercial audio, corpus masters, Demucs weights, or generated measurements containing source
content. The open-source license is still pending an explicit project decision.
