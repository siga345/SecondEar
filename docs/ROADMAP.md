# Roadmap

The roadmap is ordered by evidence and architectural learning, not feature count. Scope may change as
implementation options are evaluated.

## Phase 0: Foundation and decisions — current

- Establish product language and non-goals.
- Establish monorepo boundaries.
- Define the conceptual metric, finding, confidence, and versioning model.
- Compare decoder, dependency management, API contract, upload, and testing options.
- Select an open-source license.
- Define acceptance criteria before starting the first implementation.

## Phase 1: Technical metadata vertical slice

- Upload WAV, FLAC, and MP3.
- Validate declared and decoded input.
- Decode audio through the selected adapter.
- Measure duration, sample rate, and channel count.
- Return a typed FastAPI response.
- Render the result in a strict Next.js interface.
- Cover the domain and API with synthetic and malformed inputs.
- Add local development commands, Docker support if useful, and stable CI.

## Phase 2: Objective level measurements

Candidate scope: sample peak, RMS, clipping indicators, DC offset, silence handling, crest factor, and
integrated loudness. True peak should be included only after its oversampling method and conformance
tests are defensible.

## Phase 3: Frequency and stereo measurements

Candidate scope: spectral centroid, rolloff, configurable frequency-band energy, channel balance,
inter-channel correlation, and carefully defined width indicators.

## Phase 4: Timelines and visual evidence

Candidate scope: waveform, RMS and peak timelines, spectrogram, frequency distribution, stereo
correlation timeline, and macro-dynamic variation. Time-series storage and downsampling contracts
must be decided before implementation.

## Later research phases

Rhythm, anonymous structural segmentation, arrangement development, harmony, melody, performance,
manually supplied lyrics, reference comparison, and documented derived indices may follow. Each needs
its own evidence model, confidence policy, test fixtures, and applicability rules.

Semantic structure labels, source separation, ML models, authentication, persistent storage,
asynchronous jobs, and any LLM explanation layer remain deferred until justified by a concrete use
case.
