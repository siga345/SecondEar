# Architecture

## Goals

The architecture must protect the analytical domain from delivery frameworks and make every result
explainable, versioned, testable, and serializable. The first implementation should remain a modular
monolith in a monorepo.

## Implemented Mixing boundary

```text
Python API / CLI
  -> SoundFile decoder and input policy
  -> direct DSP + libebur128 adapters
  -> Demucs source-separation adapter
  -> profile registry and scoring engine
  -> typed MixingResult
```

The analysis package is implemented independently of delivery frameworks. Future FastAPI and web
layers call the same API after full-pipeline latency is measured. The public Mixing contract is
limited to lossless WAV and FLAC; isolated research tooling may accept explicitly lossy MP3 input but
cannot produce a public Mixing profile or score.

## Repository responsibilities

### `packages/analysis`

Owns analytical domain models, validation rules, decoding and pronunciation interfaces, pipeline
orchestration, measurements, and analyzer versioning. It exposes a plain Python API and does not
import FastAPI, frontend code, database clients, or external AI clients.

### `apps/api`

Owns HTTP routing, request size enforcement, upload lifecycle when applicable, transport schemas,
error mapping, and operational configuration such as CORS. It invokes the analysis package but does
not contain DSP, pronunciation, or rhyme-detection logic.

### `apps/web`

Owns file selection, upload state, result presentation, accessibility, and API transport. It does not
infer analytical conclusions from raw values. English strings should be kept separate from layout
where practical to preserve a future i18n path.

### `tests` and `fixtures`

Own integration coverage and synthetic inputs. Unit tests may live close to their package when that
improves ownership. No copyrighted commercial track or lyric should be committed as a fixture unless
its redistribution rights are explicit.

## Mixing v1 lifecycle

1. The decoder verifies extension, decoded container, lossless subtype, finite samples, two channels,
   sample rate, and decoded duration.
2. Direct analyzers extract loudness, dynamics, stereo, tonal, and integrity metrics.
3. The pinned separator estimates four roles and verifies reconstruction.
4. Element-balance metrics are calculated from active estimated roles.
5. The registry selects a released profile with exact formula and separator identities.
6. The scoring engine calculates five traceable penalty blocks, continuous raw score, and half-up
   public score when confidence is at least `0.65`.
7. An optional reference repeats the measurement path and yields metric deltas only.
8. The typed result preserves status, versions, evidence, findings, limitations, and source hash.

Client-provided filenames, extensions, and MIME types are hints, not proof of file content.

## Dependency direction

```text
apps/web  -> HTTP contract only
apps/api  -> packages/analysis
packages/analysis -> decoder abstraction and numerical libraries as selected
```

The analysis package does not depend on either application. Domain code should receive paths,
streams, or decoded data through explicit interfaces rather than global framework state.

## Configuration

Environment-specific values should be injected at application boundaries. Mixing thresholds,
frequency bands, duration bounds, block maxima, formula version, analyzer versions, and model identity
are centralized and versioned inside the analysis package. Future transport configuration includes
API base URL, allowed web origins, maximum upload bytes, temporary directory, and concurrency limits.

## Privacy and observability

Do not serve temporary audio directly. Avoid filenames and track metadata in routine logs. Logs may
record generated request IDs, timing, result status, byte counts, and version identifiers when needed
for operations. Retention must default to deletion after synchronous analysis in the local MVP.

## Evolution rules

- Introduce persistence only when analysis history or asynchronous jobs require it.
- Introduce background processing only after measured request-duration or reliability needs justify
  it.
- Keep bounded ML estimation behind explicit adapters. A model may estimate a stem, beat, phoneme,
  or section boundary, but it must not directly assign an opaque criterion score.
- Run reference tracks through the normal analysis pipeline, then compare analysis results in a
  separate comparison engine.
- Separate observations from recommendations. A benchmark difference alone is not a recommendation.
- Prefer explicit adapters around third-party DSP and decoding libraries so domain contracts do not
  inherit unstable library types.
