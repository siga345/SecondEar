# Roadmap

The roadmap is ordered by evidence and architectural learning, not feature count. Scope may change as
implementation options are evaluated.

## Phase 0: Foundation and decisions — completed for Mixing v1

- Establish product language and non-goals.
- Establish monorepo boundaries.
- Define the conceptual metric, finding, confidence, and versioning model.
- Define and review the draft nine-criterion 90-point methodology.
- Compare decoder, dependency management, API contract, upload, and testing options.
- Define the core genre taxonomy and the calibration, validation, and holdout protocol.
- Select an open-source license.
- Define acceptance criteria before starting the first implementation.

## Phase 1: Mixing v1 research engine — implemented

- Validate and fully decode lossless stereo WAV/FLAC input from 30 through 600 seconds.
- Measure EBU loudness, dynamics, 24-band ERB energy, stereo behavior, and signal integrity.
- Estimate four stems with pinned Demucs `htdemucs_ft` and validate reconstruction.
- Derive element-balance metrics without penalizing absent roles.
- Apply the open five-block formula through version-matched genre profiles.
- Return typed results through the Python API and CLI.
- Keep optional-reference comparison separate from target scoring.
- Cover direct DSP, scoring, profile governance, integration, and conformance boundaries.

## Phase 2: Lawful corpus and profile release — current

- Obtain at least 50 rights-confirmed lossless masters for each core genre.
- Maintain 30 calibration, 10 validation, and 10 holdout tracks with no more than two per artist.
- Run the official EBU Loudness Test Set in the release environment.
- Generate profile distributions with exact analyzer and separator identities.
- Test controlled clipping, limiting, EQ, stem-balance, stereo, phase, and DC variants.
- Release a genre profile only after validation and untouched holdout gates pass.

## Phase 3: Runtime measurement and product integration

- Measure real CPU/GPU latency and memory on 30-second through 10-minute masters.
- Set upload bytes, synchronous timeout, temporary-file, and concurrency policies from those results.
- Integrate the same analysis package into the thin FastAPI layer.
- Add a web report for score, confidence, penalties, metrics, findings, and reference comparison.

## Phase 4: Timelines and expanded evidence

Candidate scope: waveform, RMS and peak timelines, spectrogram, frequency distribution, stereo
correlation timeline, and macro-dynamic variation. Time-series storage and downsampling contracts
must be decided before implementation.

## Scoring research track

- Build a lawful research corpus across genres and score ranges.
- Use 90-point tracks as upper anchors while retaining middle and lower anchors.
- Preserve review count and disagreement instead of storing only an average.
- Compare explicit SecondEar formulas with grouped human-consensus categories.
- Keep calibration, validation, and holdout sets separate.
- Permit lossy MP3 only in internal research tools and label fidelity-sensitive evidence as limited.

The provisional order for criterion research, from lower expected implementation risk to higher
research uncertainty, is:

1. Mixing
2. Rhymes
3. Rhythm
4. Structure
5. Artist Performance
6. Sound Production
7. Imagery
8. Expressive Delivery (public label: Charisma)
9. Individuality

The order is not a dependency guarantee. A criterion may remain in research while a later one moves
forward if its evidence, datasets, or validation method become ready earlier.

### Active criterion slice: Mixing

The framework-independent Mixing engine and CLI are implemented. Current work is corpus acquisition,
official conformance, controlled-defect validation, and the release of six lawful genre profiles. No
public score is emitted before the selected profile passes these gates.

English Rhymes remains a separate research slice with text-derived evidence and no public score. It
is no longer the active implementation focus.

## Later research phases

Rhythm, anonymous structural segmentation, arrangement development, harmony, melody, performance,
manually supplied lyrics, reference comparison, and documented derived indices may follow. Each needs
its own evidence model, confidence policy, test fixtures, and applicability rules.

Semantic structure labels, authentication, persistent storage, asynchronous jobs, and any LLM
explanation layer remain deferred until justified by a concrete use case. Bounded source separation
is now accepted only for Mixing measurements. A single opaque score-prediction model is not part of
the roadmap.
