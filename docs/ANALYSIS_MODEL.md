# Analysis Model

## Purpose

The analysis model records what was observed, how it was produced, and how confidently the system can
defend it. It is designed before individual analyzers so future metrics can be added without changing
the entire API.

The examples in this document are conceptual and do not yet define a final Python or JSON schema.

## Evidence types

| Type | Meaning | Typical confidence |
| --- | --- | --- |
| `measured` | Direct calculation from decoded data | Usually high, but still subject to input and algorithm applicability |
| `estimated` | Algorithmic or model-based inference | Explicit when the method can provide it |
| `derived` | Formal calculation from other declared metrics | Based on input validity and formula applicability |
| `benchmarked` | Interpretation relative to an explicit reference set | Based on both target and reference analyses |

## Metric

```json
{
  "key": "integrated_loudness",
  "value": -11.2,
  "unit": "LUFS",
  "evidence_type": "measured",
  "confidence": 1.0,
  "analyzer": "loudness",
  "analyzer_version": "0.1.0"
}
```

Required concepts are a stable key, typed value, explicit unit where applicable, evidence type,
confidence, analyzer identity, and analyzer version. Future decisions must define support for null or
unavailable values, scalar versus time-series payloads, and per-metric parameters.

## Analysis result

A complete result should contain:

- `analysis_version`
- analyzer versions
- analytical parameters
- creation time in UTC
- source identity that does not expose a public file path
- metrics
- findings when the active slice supports them
- explicit status for unavailable domains

The first slice should return only technical file metrics. It must not create placeholder scores.

## Finding

A finding is a neutral evidence-backed statement, not a metric and not a simulated opinion.

```json
{
  "id": "no_digital_clipping_detected",
  "category": "technical_audio",
  "title": "No digital clipping detected",
  "description": "No decoded sample exceeded the documented clipping threshold.",
  "evidence": ["sample_peak", "clipped_sample_count"],
  "confidence": 1.0,
  "severity": "info"
}
```

Allowed severity language should remain operational and neutral: `info`, `notice`, and `warning`.
The finding above is illustrative and is outside the first implementation slice.

## Confidence

Confidence represents certainty or reliability of an analytical result. It is not a measure of song
quality and is not a penalty applied to a score. A system may decline to emit a result when confidence
or applicability is below a documented threshold.

Direct measurements should not automatically receive `1.0` without considering decoder errors,
truncated files, undefined formulas, and other applicability conditions.

## Scores

Scores are deferred. A future score is permitted only with a public formula, weights, evidence,
confidence, algorithm version, and applicability rules. Scores describe performance against named
SecondEar analytical criteria, never artistic value or listener preference.

## Reproducibility

Analyzer versions refer to algorithm behavior, not only package releases. Parameters that can change
results must be included in or referenced by an analysis record. Re-running the same audio under a
new algorithm version creates a new result rather than silently modifying the old one.
