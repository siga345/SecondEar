# Product Definition

## Purpose

Artists and producers lose analytical distance after repeated exposure to the same track. SecondEar
provides a fresh, independent view by reporting properties that can be measured, computationally
estimated, formally derived, or compared with explicit references.

SecondEar evaluates evidence, not taste. It may produce direct criticism and scores against published
criteria, but it must not impersonate a listener or present personal preference as analysis.

## Product principles

1. **Objectivity over simulated opinion.** Report observable or formalizable properties only.
2. **Evidence over authority.** Important findings expose their supporting metrics and algorithms.
3. **Honest uncertainty.** Estimated results include confidence; unsupported properties remain
   unevaluated.
4. **Reproducibility.** Versions and parameters make analytical results repeatable.
5. **Neutral comparison.** Difference from a reference is not automatically a defect.
6. **Privacy by default.** Uploaded music may be unreleased intellectual property.
7. **Incremental delivery.** Each vertical slice must be useful, narrow, and thoroughly tested.

## Intended users

- Artists seeking analytical distance from familiar material.
- Producers and recording or mixing engineers checking technical properties.
- Music technologists exploring explainable DSP and MIR outputs.

## Non-goals

SecondEar does not determine whether a song is beautiful, emotionally powerful, enjoyable, or likely
to be popular. It does not score vibe, atmosphere, emotional impact, or universal artistic value. It
may identify a weak result under a named SecondEar criterion when the conclusion is supported by the
criterion's evidence and applicability rules.

The UI may use Charisma as a familiar label only for the formalized Expressive Delivery criterion. It
does not measure emotional belief or listener attachment. SecondEar is not an LLM wrapper and must not
depend on an external AI service for core use.

## 90-point methodology

The draft methodology contains nine criteria worth up to 10 points each:

1. Rhymes
2. Imagery
3. Structure
4. Rhythm
5. Artist Performance
6. Mixing
7. Sound Production
8. Individuality
9. Charisma

The first four emphasize phonetic, linguistic, structural, and rhythmic construction. Artist
Performance evaluates only the vocal or rap part and uses the internal key `vocal_performance`.
Instrumental execution, arrangement, and sound design belong to Sound Production. Individuality is
defined as statistical distinctiveness. Charisma uses the internal key `expressive_delivery` and is
defined as controlled vocal variation rather than psychological charisma.

The methodology, limitations, calibration policy, and unresolved formula decisions are documented in
`docs/SCORING.md`.

## Long-term analytical domains

The long-term product may cover technical audio, loudness, spectrum, stereo and phase, dynamics,
rhythm, non-semantic structure, arrangement development, harmony, melody, performance, lyrics,
reference comparison, and explicitly defined derived indices.

Each domain is optional until its evidence, algorithms, confidence model, applicability rules, and
tests are documented. Semantic section names such as verse or chorus should not be asserted when the
system can only defend anonymous boundaries such as Section A or Section B.

## First implemented criterion slice

Mixing v1 accepts one lossless stereo WAV/FLAC master from 30 seconds through 10 minutes, one of six
core genres, and an optional lossless reference. It measures technical integration, uses bounded
source separation for element-balance evidence, and calculates an open five-block score only when a
lawful released profile exists. MP3 is not a product Mixing format.

The initial surface is a Python API and CLI. It deliberately excludes persistence, user accounts,
recommendations, and AI-generated opinion. FastAPI and the web report follow after actual separation
latency and resource requirements are measured.

## Initial interface direction

The interface should resemble a professional analytical tool rather than a chatbot. The first page
requires only a file drop area, accepted format guidance, an explicit analyze action, clear neutral
errors, and a technical result summary.

English is the only initial UI language. User-facing strings should be organized so a future i18n
layer can replace them without rewriting analysis logic.
