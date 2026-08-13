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

SecondEar is not an artificial music critic. It must not claim emotions, enjoyment, taste,
charisma perception, artistic intuition, or knowledge of what listeners will like. Do not produce
subjective statements such as "this is a good song," "the chorus is emotional," or "the track has
great vibes." If a property cannot be evaluated with defensible evidence, return `not_evaluated` or
`insufficient_data` instead of inventing a result.

There is no core Emotion, Vibe, Atmosphere, Charisma, Emotional Impact, or Enjoyment module.

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
describes a neutral, evidence-backed observation and cites its supporting metrics.

Preferred terminology includes analysis, measurement, metric, evidence, finding, estimate,
confidence, comparison, benchmark, and index. Use quality, good, bad, emotion, feel, vibe, and taste
only when discussing product boundaries or a rigorously defined concept.

## Scoring and confidence

- A score is never a judgment of whether a song is good.
- Every score requires a documented formula, weights, evidence, confidence, algorithm version, and
  applicability rules.
- Score and confidence are independent. Never multiply a score by confidence or lower a score merely
  because confidence is lower.
- Decline to calculate a score when the applicability or confidence threshold is not met.
- Prefer deterministic scoring and derivation. There must be no hidden AI opinion.

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
microservices, Kubernetes, ML, or source separation until a concrete slice requires them.

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

The repository is currently in architecture and decision exploration. Do not implement the audio
pipeline or commit to production dependencies until the project owner explicitly selects an option
or asks to begin implementation. Record candidate approaches and trade-offs in
`docs/DECISIONS.md`.

The first implementation slice, once authorized, is strictly:

```text
upload -> validate -> decode -> duration/sample rate/channel count
       -> typed result -> FastAPI response -> Next.js display
```

It excludes loudness, spectrum, stereo analysis, dynamics, scoring, reference mode, structure
detection, ML, LLMs, authentication, and persistence.

Before adding an analytical feature, answer:

1. What exactly is being measured?
2. Is it measured, estimated, derived, or benchmarked?
3. What evidence supports it?
4. How is confidence represented?
5. Can it be reproduced and tested?
6. Does any wording accidentally present subjective interpretation as objective fact?
