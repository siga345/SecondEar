# Product Definition

## Purpose

Artists and producers lose analytical distance after repeated exposure to the same track. SecondEar
provides a fresh, independent view by reporting properties that can be measured, computationally
estimated, formally derived, or compared with explicit references.

SecondEar evaluates evidence, not taste. It must not impersonate a listener or critic.

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

SecondEar does not determine whether a song is good, beautiful, original, emotionally powerful, or
likely to be popular. It does not score vibe, atmosphere, charisma, enjoyment, emotional impact, or
artistic value. It is not an LLM wrapper and must not depend on an external AI service for core use.

## Long-term analytical domains

The long-term product may cover technical audio, loudness, spectrum, stereo and phase, dynamics,
rhythm, non-semantic structure, arrangement development, harmony, melody, performance, lyrics,
reference comparison, and explicitly defined derived indices.

Each domain is optional until its evidence, algorithms, confidence model, applicability rules, and
tests are documented. Semantic section names such as verse or chorus should not be asserted when the
system can only defend anonymous boundaries such as Section A or Section B.

## First vertical slice

The initial working product will accept WAV, FLAC, and MP3 files, validate and decode the audio,
measure duration, sample rate, and channel count, return a typed response through FastAPI, and display
the values in a simple Next.js interface.

This slice deliberately excludes persistence, user accounts, scoring, findings, references, advanced
analysis, and AI. Its purpose is to prove the boundaries between the web client, API, and reusable
analysis engine.

## Initial interface direction

The interface should resemble a professional analytical tool rather than a chatbot. The first page
requires only a file drop area, accepted format guidance, an explicit analyze action, clear neutral
errors, and a technical result summary.

English is the only initial UI language. User-facing strings should be organized so a future i18n
layer can replace them without rewriting analysis logic.
