# Open Technical Decisions

This document keeps implementation choices reversible while SecondEar is in its architecture phase.
No candidate listed here is selected unless its status changes to **Accepted** in a dated decision
record.

## D-001: Audio decoding strategy

**Status:** Open

### Candidate A: PyAV backed by FFmpeg

- Provides frame-level decoding for WAV, FLAC, and MP3 through a typed Python API.
- Makes a full decode pass and sample-count duration calculation straightforward.
- Adds native wheels and FFmpeg coupling that must be validated across supported platforms.

### Candidate B: `soundfile` plus a separate MP3 path

- Offers a small numerical interface and strong WAV/FLAC support through libsndfile.
- MP3 availability depends on the installed libsndfile build and may differ by environment.
- A fallback path can create inconsistent behavior unless carefully isolated and tested.

### Candidate C: FFmpeg/ffprobe subprocess adapter

- Uses a mature and widely available media tool with explicit control over probe and decode commands.
- Requires binary installation, subprocess hardening, timeout handling, and careful parsing.
- Can keep codec complexity outside the Python process.

### Acceptance questions

- Does every supported deployment receive consistent WAV, FLAC, and MP3 decoding?
- Can duration be verified from decoded samples instead of only container metadata?
- How are malformed, truncated, empty, and mislabeled files reported?
- What are the licensing and redistribution implications?
- How easy is deterministic synthetic-fixture testing on macOS, Linux, and Docker?

## D-002: Python environment and packaging

**Status:** Open

Candidates include standard `pyproject.toml` with `uv`, Poetry, or standard `venv` plus pip. The final
choice should provide reproducible lock files, editable monorepo packages, simple CI, and a low setup
burden for open-source contributors.

## D-003: JavaScript package management

**Status:** Open

Candidates include npm workspaces, pnpm workspaces, or keeping the initial web application independent
until a second JavaScript package exists. The decision should optimize contributor simplicity and
deterministic installs, not hypothetical scale.

## D-004: Domain metric representation

**Status:** Open

The conceptual model is stable, but the concrete representation needs decisions about generic values,
time series, unavailable states, parameter provenance, and whether core models use Pydantic,
dataclasses, or a domain model plus separate transport schema.

The chosen design must preserve static typing, stable serialization, validation, framework
independence, and future extensibility without turning every metric into untyped JSON.

## D-005: Upload transport and resource limits

**Status:** Open

The first slice can use synchronous multipart upload with chunked temporary-file writing. Before
implementation, define maximum bytes, maximum decoded duration, timeout behavior, temporary storage
location, cleanup guarantees, MIME and signature checks, and whether the API streams or buffers each
request.

Direct-to-object-storage uploads and background jobs are explicitly deferred until scale or request
duration justifies them.

## D-006: Duration definition

**Status:** Open

Candidate definitions are decoded sample count divided by sample rate, decoded timestamps, or trusted
container duration. Decoded sample count is easy to explain for constant-rate streams, while MP3
encoder delay, padding, variable timestamps, and truncated inputs require explicit policy and tests.

The API should name the measurement and document its method rather than presenting ambiguous
precision.

## D-007: API shape

**Status:** Open

Options include a generic metric collection aligned with the long-term analysis model, a strongly
typed technical-summary object for the first slice, or both through a versioned envelope. The choice
must balance frontend ergonomics, stable public contracts, and the ability to add metrics without
redesigning every client.

## D-008: Local development and containers

**Status:** Open

Docker Compose can normalize native decoder and frontend environments, but requiring containers may
slow ordinary development. A likely target is first-class native commands plus an optional Compose
path once dependency choices are accepted.

## D-009: CI baseline

**Status:** Open

CI should be added with executable code, not as an empty ceremony. Candidate checks include Python
format/lint/type/test, TypeScript lint/type/test/build, dependency lock verification, and a minimal
cross-platform decoder matrix. Exact versions follow the packaging decisions.

## D-010: Open-source license

**Status:** Open

The repository needs an explicit license before meaningful public distribution. MIT, Apache-2.0, and
copyleft alternatives have materially different patent and redistribution terms; the project owner
should select one intentionally.
