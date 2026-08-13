# Open Technical Decisions

This document keeps implementation choices reversible while SecondEar is in its architecture phase.
No candidate listed here is selected unless its status changes to **Accepted** in a dated decision
record.

## D-001: Audio decoding strategy

**Status:** Accepted for Mixing v1 on 2026-08-14

Mixing v1 uses `soundfile` backed by libsndfile for product WAV/FLAC decoding. It verifies the decoded
container against the suffix, accepts only lossless PCM or floating-point subtypes, reads every frame,
calculates duration from decoded frame count, and rejects non-finite samples. Research MP3 support is
separate and cannot produce fidelity-sensitive Mixing scores.

The production decoder must support WAV and FLAC. Internal research tooling may additionally support
MP3, but the research path must mark it as lossy and must not make fidelity-sensitive scoring claims
that are equivalent to lossless product input.

### Candidate A: PyAV backed by FFmpeg

- Provides frame-level decoding for WAV, FLAC, and research MP3 through a typed Python API.
- Makes a full decode pass and sample-count duration calculation straightforward.
- Adds native wheels and FFmpeg coupling that must be validated across supported platforms.

### Candidate B: `soundfile` plus a separate MP3 path

- Offers a small numerical interface and strong product-format support through libsndfile.
- Research MP3 availability depends on the installed libsndfile build and may differ by environment.
- A separate research fallback can create inconsistent behavior unless carefully isolated and tested.

### Candidate C: FFmpeg/ffprobe subprocess adapter

- Uses a mature and widely available media tool with explicit control over probe and decode commands.
- Requires binary installation, subprocess hardening, timeout handling, and careful parsing.
- Can keep codec complexity outside the Python process.

### Acceptance questions

- Does every supported deployment receive consistent WAV and FLAC decoding?
- Can internal research MP3 support remain isolated from the product contract?
- Can duration be verified from decoded samples instead of only container metadata?
- How are malformed, truncated, empty, and mislabeled files reported?
- What are the licensing and redistribution implications?
- How easy is deterministic synthetic-fixture testing on macOS, Linux, and Docker?

## D-002: Python environment and packaging

**Status:** Accepted for the analysis package on 2026-08-14

The analysis package uses Python 3.12 and standard `pyproject.toml` packaging with setuptools. It is
installable through pip in a standard virtual environment. Demucs and Torch are an optional
`separation` extra so direct development tools can remain lightweight. A deterministic lock-file
workflow remains a future repository-level decision.

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

Mixing v1 fixes only the analytical duration boundary: decoded audio must be from 30 through 600
seconds. HTTP byte size, timeout, and concurrency remain open until Demucs runtime is measured.

## D-006: Duration definition

**Status:** Accepted for WAV/FLAC on 2026-08-14

Candidate definitions are decoded sample count divided by sample rate, decoded timestamps, or trusted
container duration. Decoded sample count is easy to explain for constant-rate streams, while MP3
encoder delay, padding, variable timestamps, and truncated inputs require explicit policy and tests.

For the accepted lossless product formats, duration is decoded frame count divided by decoded sample
rate. The source is fully decoded and validated. Lossy research timing remains outside this decision.

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

## D-011: Product input format policy

**Status:** Accepted on 2026-08-14

The product accepts lossless WAV and FLAC. MP3 is excluded from the public upload contract because it
cannot support the same fidelity-sensitive analysis as lossless input.

Internal research tools may accept MP3 for early comparison of structure, rhythm, lyrics, and other
features that tolerate lossy input. Every such analysis must record the lossy codec and restrict or
decline affected Mixing measurements and scores.

## D-012: Overall scoring and unavailable criteria

**Status:** Open

The draft methodology defines nine criteria with a nominal maximum of 90 points. The following remain
unresolved:

- whether all nine criteria have equal overall weight;
- whether the four parent groups have equal weight despite containing different numbers of criteria;
- how non-Mixing criteria round and how their internal continuous values are exposed; Mixing v1
  retains `raw_score` and publishes a half-up integer;
- whether an overall score is withheld when any criterion is unavailable;
- whether a partial result can have a separate scale without misleading comparison.

Unavailable criteria must never silently become zero or be rescaled without an accepted public rule.

## D-013: Core genre taxonomy

**Status:** Accepted for Mixing v1 on 2026-08-14

Mixing v1 requires exactly one primary genre from `rap`, `pop`, `r_and_b`, `rock`, `country`, and
`electronic`. Unsupported genres return a non-scoring status. Each genre selects a separately
versioned measurement profile; it does not alter a hidden prompt. Mixed genres, secondary tags,
subgenres, and fallback rules remain future work.

## D-014: Scoring calibration strategy

**Status:** Accepted on 2026-08-14

SecondEar will not train a single opaque model to predict review scores. Criterion scores will be
produced by explicit and versioned mechanisms. The project owner will manually compare fixed
SecondEar versions with aggregate human scores and review evidence, then use those comparisons to
guide documented formula, feature, threshold, or genre-profile revisions.

Manual adjustment is still a form of calibration and can overfit. Research data must therefore be
split into calibration, validation, and holdout sets. Tracks receiving 90 points are valuable upper
anchors, but the corpus must also include middle and lower score ranges to define the complete scale.

Human consensus is a benchmark, not ground truth. Store review count and score disagreement alongside
aggregates. Exclude Atmosphere / Vibe from the SecondEar target. Do not automate collection or
redistribute third-party audio or review text until access terms, copyright, and permission are
resolved.

## D-015: Criterion meanings

**Status:** Accepted as draft methodology 0.1 on 2026-08-14

The public 90-point model contains Rhymes, Imagery, Structure, Rhythm, Artist Performance, Mixing,
Sound Production, Individuality, and Charisma. Their internal meanings are fixed for the current
methodology as:

- phonetic and rhyme construction;
- linguistic imagery and figurative construction;
- structural organization and development;
- rhythmic design and controlled variation;
- technical control of the vocal or rap performance only;
- technical mix integrity;
- instrumental arrangement and sonic construction;
- statistical distinctiveness;
- controlled expressive vocal delivery.

The public Charisma label maps to `expressive_delivery`; it does not represent whether the software
believes or emotionally responds to the artist. Exact formulas and thresholds remain open.

## D-016: Initial language scope for lyrical criteria

**Status:** Superseded by D-017 on 2026-08-14

Russian (`ru`) is the first supported analysis language for Rhymes and, later, Imagery. This choice
limits the first language profile; it does not make the domain models or analyzer interfaces
Russian-specific. Stress, pronunciation, phoneme similarity, morphology, lexical resources, corpus
baselines, and thresholds must be isolated behind versioned language profiles so English and other
languages can be added without changing criterion semantics.

The first Rhymes research stage accepts manually supplied, line-broken Russian lyrics. Lyrics
transcription, lyric-to-audio alignment, and performed-pronunciation correction remain deferred.
Unsupported, mixed-language, or insufficient inputs must return `not_evaluated` or
`insufficient_data`, not a zero score.

Repository content and the initial product interface remain English as required by the project
language policy. Russian-first support refers to the language of analyzed lyrics, not the language of
source code, documentation, schemas, findings, or UI copy.

## D-017: English-first Rhymes implementation

**Status:** Accepted on 2026-08-14

English replaces Russian as the first implemented language for the Rhymes criterion. The complete
0.1 slice accepts manually supplied, line-broken lyrics and supports caller-selected `en-US` and
`en-GB` pronunciation profiles. It parses pinned official CMU Pronouncing Dictionary and Britfone
3.0.1 data through repository-owned adapters and permits occurrence-level ARPAbet or IPA overrides
for names, slang, dialect forms, homographs, and out-of-vocabulary tokens.

The implementation must return traceable pronunciation choices, rhyme pairs, families, schemes,
metrics, analyzer version, dictionary fingerprint, confidence, and applicability. It may not infer a
performed pronunciation from text alone. Audio transcription and alignment remain later stages.

A deterministic public 1--10 score is emitted when the documented applicability gates pass. Formula
0.1, six genre-weight profiles, seed piecewise-linear anchors, independent confidence, and validation
targets are published in `docs/SCORING.md`. The seed anchors are explicitly provisional until the
owner corpus is calibrated and validated. Recognition cohorts are not automatic high scores.

Commercial song lyrics and audio, including Grammy-recognized works, must not be downloaded,
redistributed, or committed without the necessary rights. Research runs may analyze lawfully
obtained local material and store derived results without storing the source lyrics or audio.

## D-018: Mixing v1 analytical contract

**Status:** Accepted on 2026-08-14

Mixing v1 evaluates the combined technical result of mixing and mastering from one final stereo
master. Accepted inputs are lossless WAV/FLAC, at least 44.1 kHz, and 30--600 seconds. Lyrics are not
required. An optional reference is analyzed through the same pipeline and produces only comparison
metrics; it never changes the target score.

The engine measures five penalty blocks: element balance (4.0 maximum), stereo field (3.0), tonal
balance (2.5), loudness and dynamics (2.0), and signal integrity (2.0). The raw score starts at 10,
subtracts the five penalties, and is clamped to 1--10. The public score uses half-up integer rounding.
Confidence remains independent; no score is emitted below `0.65`.

Demucs v4 `htdemucs_ft` estimates `vocals`, `drums`, `bass`, and `other` only for measurement. The
model cannot assign a score. Results record the implementation version, model-state checksum, Torch,
and Torchaudio versions. Separation output has confidence capped at `0.8` and must pass reconstruction
validation or the result becomes `insufficient_data` while direct metrics are retained.

Genre-relative profile distributions store median, Q10, Q90, and MAD. Values inside Q10--Q90 receive
no penalty; outside distance is normalized through MAD and reaches full severity two robust scales
beyond the range. Block severity is `0.7 * worst + 0.3 * mean`. Signal integrity uses documented fixed
thresholds, including no true-peak penalty through `0 dBTP`, full severity at `+1 dBTP`, and DC
severity from `-60` through `-40 dBFS`.

No genre profile may be released with fewer than 30 calibration, 10 validation, and 10 holdout
rights-confirmed lossless masters, more than two tracks per artist, fewer than two represented
substyles or periods, mixed analyzer or separator identities, failed EBU conformance, or failed
validation or holdout. Audio and model weights are not committed. MP3 and RZT scores remain research
comparisons and cannot define public Mixing profiles.
