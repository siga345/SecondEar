# Architecture

## Goals

The architecture must protect the analytical domain from delivery frameworks and make every result
explainable, versioned, testable, and serializable. The first implementation should remain a modular
monolith in a monorepo.

## Proposed system boundary

```text
Browser
  |
  | multipart upload / structured JSON
  v
FastAPI application
  |
  | local Python call
  v
Analysis package
  |
  | decoder adapter
  v
Audio decoder
```

This is a proposal, not a commitment to a particular decoder library.

## Repository responsibilities

### `packages/analysis`

Owns analytical domain models, validation rules that depend on decoded audio, decoder interfaces,
pipeline orchestration, measurements, and analyzer versioning. It must expose a plain Python API and
must not import FastAPI, frontend code, database clients, or external AI clients.

### `apps/api`

Owns HTTP routing, request size enforcement, temporary upload lifecycle, transport schemas, error
mapping, and operational configuration such as CORS. It invokes the analysis package but does not
contain DSP or format-specific decoding logic.

### `apps/web`

Owns file selection, upload state, result presentation, accessibility, and API transport. It does not
infer analytical conclusions from raw values. English strings should be kept separate from layout
where practical to preserve a future i18n path.

### `tests` and `fixtures`

Own integration coverage and synthetic audio inputs. Unit tests may live close to their package when
that improves ownership. No copyrighted commercial track should be committed as a fixture unless its
redistribution rights are explicit.

## First-slice request lifecycle

1. The browser rejects obviously unsupported extensions for immediate feedback.
2. The API independently enforces the supported-format list and upload size limit.
3. The API writes to a non-public temporary location using a generated identifier.
4. The analysis package invokes the selected decoder and requires decodable audio frames.
5. File-level measurements are returned through the domain model.
6. The API maps the result into a stable JSON contract.
7. The temporary upload is deleted in guaranteed cleanup logic.
8. The web client renders the technical measurements and neutral errors.

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

Environment-specific values should be injected at application boundaries. Candidate first-slice
configuration includes API base URL, allowed web origins, maximum upload bytes, temporary directory,
accepted formats, and log level. Analytical thresholds and frequency bands will require typed,
versioned configuration when those features are introduced.

## Privacy and observability

Do not serve temporary audio directly. Avoid filenames and track metadata in routine logs. Logs may
record generated request IDs, timing, result status, byte counts, and version identifiers when needed
for operations. Retention must default to deletion after synchronous analysis in the local MVP.

## Evolution rules

- Introduce persistence only when analysis history or asynchronous jobs require it.
- Introduce background processing only after measured request-duration or reliability needs justify
  it.
- Run reference tracks through the normal analysis pipeline, then compare analysis results in a
  separate comparison engine.
- Separate observations from recommendations. A benchmark difference alone is not a recommendation.
- Prefer explicit adapters around third-party DSP and decoding libraries so domain contracts do not
  inherit unstable library types.
