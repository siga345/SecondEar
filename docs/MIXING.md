# Mixing v1

**Engine status:** Implemented

**Public profile status:** Not released

**Formula version:** `mixing-score-0.1.0`

**Last updated:** 2026-08-14

## Scope

Mixing v1 evaluates the technical quality of one final stereo master: the combined result of mixing
and mastering. It does not evaluate arrangement choices, instrumental performance, emotion, taste,
or likely audience response.

Accepted input:

- WAV or FLAC whose decoded container agrees with the extension;
- exactly two channels;
- sample rate of at least 44.1 kHz;
- decoded duration from 30 through 600 seconds;
- one primary genre: `rap`, `pop`, `r_and_b`, `rock`, `country`, or `electronic`;
- an optional WAV/FLAC reference satisfying the same audio constraints.

Lyrics are not an input to Mixing. Mono, multichannel, lossy, malformed, mislabeled, non-finite,
too-short, and too-long inputs return a non-scoring status with no artificial zero.

## Pipeline

```text
SoundFile/libsndfile full decode
  |
  +-- libebur128 loudness, LRA, sample peak, and true peak
  +-- direct integrity, stereo, and 24-band ERB measurements
  +-- Demucs htdemucs_ft -> vocals, drums, bass, other
        |
        +-- relative stem loudness, temporal stability, and ERB audibility proxies
  |
  +-- version-matched genre profile
        |
        +-- five penalty blocks -> raw score -> half-up public score
```

Demucs is an estimator, not the judge. Its pinned `htdemucs_ft` weights provide measurements to the
open formula. Every result records the Demucs version, model name, model-state SHA-256, Torch version,
and Torchaudio version. Estimated-stem results have confidence capped at `0.8`.

Source separation must pass reconstruction validation. The sum of the returned stems must reproduce
the input within the documented residual threshold. If separation fails, lacks an expected role, or
produces invalid samples, direct measurements are retained but the result becomes
`insufficient_data`.

## Formula

```text
raw_score = clamp(
    10
    - element_balance_penalty
    - stereo_penalty
    - tonal_penalty
    - dynamics_penalty
    - integrity_penalty,
    1,
    10
)
```

The public score is an integer rounded half-up. `raw_score` is stored at full available precision for
calibration and reproducibility. Confidence is independent and never multiplied into the score. If
final confidence is below `0.65`, no score is emitted.

| Block | Maximum penalty | v1 evidence |
| --- | ---: | --- |
| Element balance | 4.0 | Relative stem LUFS, short-term ratio stability, active-role count, 24-band ERB audibility and masking proxies |
| Stereo field | 3.0 | L/R balance, mid/side energy by band, correlation distribution, negative-correlation rate, mono fold-down |
| Tonal balance | 2.5 | Relative power in 24 ERB-spaced bands and persistent spectral behavior |
| Loudness and dynamics | 2.0 | Gain-relative short-term LUFS relationships, LRA, crest factor, peak-to-loudness relationship |
| Signal integrity | 2.0 | Sample/true peak, clipping rate and runs, DC offset, invalid decoded data |

The first four blocks are benchmarked against the selected genre profile. Every feature distribution
stores median, Q10, Q90, and MAD. Values inside Q10--Q90 have zero severity. Outside that range, the
distance is normalized by MAD and reaches full severity two robust scales beyond the accepted bound.
The block severity is:

```text
0.7 * worst_feature_severity + 0.3 * mean_feature_severity
```

Signal-integrity thresholds are deterministic rather than genre-relative. True peak is unpenalized
through `0 dBTP` and reaches full severity at `+1 dBTP`. DC severity grows from `-60 dBFS` to full at
`-40 dBFS`. Click/pop candidates and suspected dropouts are reserved as experimental findings and do
not affect v1 scoring.

Absolute integrated and short-term LUFS remain measured and available for reference comparison, but
they do not enter the v1 penalty formula. Gain-relative LUFS relationships and dynamics do. Therefore
a uniform gain change within true-peak headroom does not change the Mixing score; overload still can.

An absent or inactive estimated stem is omitted from balance comparisons; it is never penalized as a
bad mix merely because the composition does not contain that role.

## Result contract

The Python API is:

```python
analyze_mixing(
    audio_path,
    primary_genre,
    reference_path=None,
) -> MixingResult
```

`MixingResult` carries status, public score, continuous raw score, independent confidence, source
hash, analysis/formula/profile/analyzer/model versions, raw metrics, five penalty blocks, traceable
findings, limitations, separator identity, and a separate reference comparison.

An optional reference passes through the same direct and separation analyzers. Its metric deltas are
reported separately and cannot change the target profile, target penalties, raw score, integer score,
or confidence. A failed reference analysis limits only `reference_comparison`.

## Genre profiles and corpus governance

The repository intentionally ships no released Mixing profile. A profile is not a hand-written set
of plausible targets: it must be generated from a lawful corpus using exactly the analyzer, formula,
and separator versions recorded by the profile.

Each of the six genres needs at least 50 rights-confirmed lossless masters:

- 30 calibration;
- 10 validation;
- 10 holdout;
- no more than two tracks from one artist;
- unique audio hashes and track identifiers;
- varied substyles and periods.

Corpus audio and Demucs weights must not be committed. Store only the manifest, provenance, hashes,
derived metrics, split, and analyzer identities. Release mode additionally requires recorded EBU
conformance, validation, and holdout passes. Formula, separator, or corpus changes require a new
profile version.

The CLI supports the lawful workflow:

```bash
secondear-mixing observe master.wav \
  --genre rap \
  --track-id track-001 \
  --artist-id artist-001 \
  --substyle alternative-rap \
  --period 2020s \
  --split calibration \
  --rights-confirmed >> observations.jsonl

secondear-mixing build-profile observations.jsonl profiles/mixing/rap.json \
  --version mixing-rap-1.0.0 \
  --release \
  --ebu-passed \
  --validation-passed \
  --holdout-passed
```

MP3 files and RZT review scores belong only to the research comparison loop. They must not produce or
populate public Mixing profiles.

## Verification

The default test suite uses generated WAV/FLAC signals and injected deterministic separators. It
covers input validation, silence safety, loudness and spectral metrics, L/R swap invariance, overall
gain invariance for genre-relative scoring, monotonic defect penalties, absent stems, profile release
gates, unreliable separation, reference score isolation, and deterministic serialization.

The real-model smoke test is opt-in because it downloads and runs large weights:

```bash
SECONDEAR_RUN_DEMUCS=1 python -m pytest -q tests/test_demucs_integration.py
```

Official EBU conformance files are not redistributed. Obtain the
[EBU Loudness Test Set](https://tech.ebu.ch/publications/ebu_loudness_test_set) directly, then run:

```bash
SECONDEAR_EBU_TEST_SET=/absolute/path/to/ebu/files \
  python -m pytest -q -m ebu tests/test_ebu_conformance.py
```

The tests use the published tolerances encoded beside each official sequence. A profile must not be
released when these tests, validation, or holdout fail.

## Known limitations

- No public score is available until a released profile exists for the selected genre.
- Demucs estimation can confuse overlapping, processed, sparse, or unusual sources; confidence is
  capped and reconstruction is checked, but semantic stem correctness is not guaranteed.
- CPU analysis is substantially slower than audio duration on some machines; FastAPI and web
  integration wait for production-scale latency measurement.
- v1 stereo and tonal metrics are whole-track and short-window technical proxies, not semantic mix
  judgments.
- Click/pop and dropout detection is experimental and non-scoring.
- A single core genre cannot fully describe hybrid material; mixed and subgenre profiles are future
  work.
