# SecondEar Agent Guide

This file is the durable working agreement for contributors and coding agents in this repository.
Read it before proposing or making changes.

## Communication and language

- The project owner may communicate in Russian.
- All repository content must be written in English: source code, identifiers, comments, docstrings,
  UI copy, errors, tests, configuration, documentation, API fields, and commit-oriented naming.
- The frontend should remain compatible with a future internationalization layer, but English is the
  only supported language for now.

## Product definition

SecondEar is an open-source objective music analysis system for artists, producers, engineers, and
music technologists. It uses digital signal processing, music information retrieval, and
computational analysis to provide an independent, evidence-based view of a track.

The product promise is:

> No taste. No attachment. Just evidence.

The supporting idea is:

> Hear what familiarity hides.

SecondEar is not a simulated human critic. It may issue direct critical conclusions and criterion
scores, including identifying weak structure, rhythmic monotony, unstable vocal execution, or
technical mix problems, only when the conclusion follows from a published criterion and traceable
evidence. It must not claim personal emotions, enjoyment, taste, artistic intuition, or knowledge of
what listeners will like.

Do not produce unsupported statements such as "this is a bad song," "the chorus is emotional," or
"the track has great vibes." If a property cannot be evaluated with defensible evidence, return
`not_evaluated` or `insufficient_data` instead of inventing a result.

There is no Emotion, Vibe, Atmosphere, Emotional Impact, or Enjoyment score. The public Charisma label
is permitted only as the documented `expressive_delivery` criterion: controlled variation in vocal
timing, dynamics, pitch, and timbre. It must not be defined as whether the software "believes" the
artist.

## Evidence model

Every analytical result must declare one of these evidence types:

- `measured`: a direct mathematical or signal-processing measurement.
- `estimated`: an inference from an algorithm, MIR method, or model; include confidence when
  possible.
- `derived`: a higher-level property calculated from declared input metrics.
- `benchmarked`: an interpretation relative to an explicit comparison set.

Important findings must be traceable through this chain:

```text
finding -> evidence -> metric -> analyzer -> algorithm/version
```

Metrics and findings are distinct. A metric records a value such as integrated loudness. A finding
describes an evidence-backed observation or criticism and cites its supporting metrics.

Preferred terminology includes analysis, measurement, metric, evidence, finding, estimate,
confidence, comparison, benchmark, and index. Use quality, good, bad, emotion, feel, vibe, and taste
only when discussing product boundaries or a rigorously defined concept.

## Scoring and confidence

- A score expresses performance against a named and published SecondEar criterion. It is not a claim
  of universal artistic truth or personal preference.
- Every score requires a documented formula, weights, evidence, confidence, algorithm version, and
  applicability rules.
- Score and confidence are independent. Never multiply a score by confidence or lower a score merely
  because confidence is lower.
- Decline to calculate a score when the applicability or confidence threshold is not met.
- Prefer deterministic scoring and derivation. There must be no hidden AI opinion.

The draft 90-point methodology is defined in `docs/SCORING.md`. Its nine public criteria are Rhymes,
Imagery, Structure, Rhythm, Artist Performance, Mixing, Sound Production, Individuality, and Charisma.
Their internal meanings are phonetic construction, linguistic imagery, structural development,
rhythmic design, vocal technical control, technical mix integrity, arrangement and sonic
construction, statistical distinctiveness, and controlled expressive delivery.

Do not train or invoke a single opaque model to assign these scores. A bounded ML component may
estimate an intermediate feature such as a vocal stem, beat, phoneme alignment, or section boundary.
The final criterion score must still be produced by a versioned and inspectable mechanism.

## Architecture boundaries

Use a monorepo with these responsibility boundaries:

- `packages/analysis`: framework-independent typed Python analysis domain and DSP/MIR pipeline.
- `apps/api`: a thin transport and orchestration layer around the analysis package.
- `apps/web`: a strict TypeScript, React, and Next.js analytical interface.
- `docs`: product, architecture, analytical model, roadmap, and decision records.
- `tests`: cross-package and end-to-end tests; package-local tests may be introduced when useful.
- `fixtures`: synthetic or explicitly redistributable test assets only.
- `scripts`: repository development and maintenance commands.

The analysis engine must remain callable without HTTP, a database, the frontend, or an external AI
service. Keep HTTP schemas separate from core domain models where their responsibilities differ.
Reference tracks must pass through the same analysis pipeline as user tracks; comparison is a
separate downstream concern.

An LLM must never be the source of analytical evidence. A future LLM integration may translate
structured findings into natural-language explanations, but the product must remain usable without
an LLM API.

Do not introduce PostgreSQL, authentication, background queues, Redis, message brokers,
microservices, Kubernetes, or an LLM dependency until a concrete slice requires them. Mixing v1 is
the accepted exception for bounded source separation: Demucs `htdemucs_ft` estimates stems only to
provide measurements to the public scoring formula and never assigns a score itself.

## Reproducibility and privacy

Each persisted or returned analysis should eventually include the analysis version, analyzer
versions, parameters, and creation time. An algorithm change creates a new analysis; it must not
silently reinterpret old results.

Treat every uploaded track as private, unreleased intellectual property:

- Use private storage by default and avoid predictable public URLs.
- Do not log audio content or unnecessary metadata.
- Keep binary storage separate from analytical results.
- Define retention and deletion behavior explicitly.
- Never use uploaded tracks for training without explicit permission.
- Prefer temporary files with guaranteed cleanup for the local MVP.

## Testing standards

DSP work must be tested with synthetic signals before relying on commercial music. Relevant fixtures
include silence, sine waves, white noise, impulses, identical and inverted stereo channels, and
left-only audio. Tests must cover numerical expectations, invalid input, boundary conditions, and
safe handling of silence without NaN or infinity propagation.

Code should be typed, explicit, modular, and testable. Public or complex APIs need useful docstrings.
Document formulas, units, thresholds, parameter defaults, and algorithm versions. Keep configurable
frequency boundaries and thresholds out of scattered magic numbers.

## Current phase

Mixing v1 is the active implemented research slice. The framework-independent engine in
`packages/analysis` validates and fully decodes one lossless stereo master, measures loudness,
dynamics, spectrum, stereo behavior, and integrity, estimates four stems with the pinned Demucs
`htdemucs_ft` model, and applies a versioned open formula only when a released genre profile exists.

The accepted product contract is:

```text
WAV/FLAC stereo master + primary genre + optional WAV/FLAC reference
  -> validate and decode
  -> direct DSP and EBU R128 measurements
  -> Demucs measurement adapter
  -> versioned genre-profile penalties
  -> MixingResult or insufficient_data
```

Inputs must be stereo, at least 44.1 kHz, and between 30 and 600 seconds. The six supported primary
genres are `rap`, `pop`, `r_and_b`, `rock`, `country`, and `electronic`. A reference passes through
the same measurement pipeline but never changes the target score. No public profile or score may be
released until the corresponding lawful corpus contains at least 30 calibration, 10 validation, and
10 holdout tracks and passes the declared release gates.

The Python API and CLI are the current product surface. FastAPI and web integration follow only
after actual full-pipeline latency and operating limits have been measured. Rhymes remains a separate
research domain but is no longer the active implementation slice.

Before adding an analytical feature, answer:

1. What exactly is being measured?
2. Is it measured, estimated, derived, or benchmarked?
3. What evidence supports it?
4. How is confidence represented?
5. Can it be reproduced and tested?
6. Is the critical conclusion limited to what the published criterion can support?
