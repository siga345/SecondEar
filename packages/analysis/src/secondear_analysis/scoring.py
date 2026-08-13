"""Inspectable penalty scoring for the Mixing criterion."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

import numpy as np

from .config import (
    ANALYSIS_VERSION,
    BLOCK_MAX_PENALTIES,
    CONFIDENCE_THRESHOLD,
    FORMULA_VERSION,
)
from .errors import ProfileError
from .models import (
    Finding,
    FindingSeverity,
    Metric,
    PenaltyBlock,
    SeparatorIdentity,
    TimeRange,
)
from .profiles import GenreProfile


@dataclass(frozen=True, slots=True)
class ScoreOutcome:
    score: int
    raw_score: float
    confidence: float
    blocks: tuple[PenaltyBlock, ...]
    findings: tuple[Finding, ...]


MIN_PROFILE_FEATURES = {
    "element_balance": 2,
    "stereo": 6,
    "tonal": 24,
    "dynamics": 5,
}

NONSCORING_PROFILE_FEATURES = {
    "dynamics.integrated_lufs",
    "dynamics.short_term_p10_lufs",
    "dynamics.short_term_p50_lufs",
    "dynamics.short_term_p90_lufs",
}


class MixingScoreEngine:
    """Calculate Mixing v1 from released profile evidence and fixed defects."""

    version = FORMULA_VERSION

    def score(
        self,
        metrics: tuple[Metric, ...],
        profile: GenreProfile,
        separator: SeparatorIdentity,
    ) -> ScoreOutcome:
        if profile.status != "released":
            raise ProfileError(
                "A public Mixing score requires a released genre profile."
            )
        if profile.analysis_version != ANALYSIS_VERSION:
            raise ProfileError("Profile and analysis pipeline versions do not match.")
        if profile.formula_version != self.version:
            raise ProfileError("Profile and score formula versions do not match.")
        if profile.separator != separator:
            raise ProfileError("Profile and target separator identities do not match.")
        target_analyzers = {
            metric.analyzer: metric.analyzer_version for metric in metrics
        }
        if profile.analyzer_versions != target_analyzers:
            raise ProfileError("Profile and target analyzer versions do not match.")

        metric_map = {metric.key: metric for metric in metrics}
        blocks: list[PenaltyBlock] = []
        findings: list[Finding] = []
        used_confidences = [profile.confidence]

        for block in ("element_balance", "stereo", "tonal", "dynamics"):
            feature_metrics = _profile_metrics_for_block(block, metric_map, profile)
            if len(feature_metrics) < MIN_PROFILE_FEATURES[block]:
                raise ProfileError(
                    f"The released profile does not cover enough {block} features for this track."
                )
            severities = {
                metric.key: profile.features[metric.key].severity(metric.value)
                for metric in feature_metrics
            }
            penalty_block = _make_block(block, severities)
            blocks.append(penalty_block)
            used_confidences.extend(metric.confidence for metric in feature_metrics)
            findings.extend(_findings_for_block(penalty_block, metric_map, profile))

        integrity_severities = _integrity_severities(metric_map)
        integrity_block = _make_block("integrity", integrity_severities)
        blocks.append(integrity_block)
        used_confidences.extend(
            metric_map[key].confidence
            for key in integrity_severities
            if key in metric_map
        )
        findings.extend(_integrity_findings(integrity_block, metric_map))

        total_penalty = sum(block.penalty for block in blocks)
        raw_score = float(np.clip(10.0 - total_penalty, 1.0, 10.0))
        confidence = min(used_confidences)
        if confidence < CONFIDENCE_THRESHOLD:
            raise ProfileError(
                "Required Mixing evidence is below the confidence threshold."
            )
        display_score = int(
            Decimal(str(raw_score)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        )
        return ScoreOutcome(
            score=display_score,
            raw_score=raw_score,
            confidence=confidence,
            blocks=tuple(blocks),
            findings=tuple(findings),
        )


def _profile_metrics_for_block(
    block: str, metric_map: dict[str, Metric], profile: GenreProfile
) -> list[Metric]:
    prefix = "element." if block == "element_balance" else f"{block}."
    excluded = {
        "element.active_role_count",
        "element.separation_residual_db",
        *NONSCORING_PROFILE_FEATURES,
    }
    return [
        metric
        for key, metric in sorted(metric_map.items())
        if key.startswith(prefix) and key not in excluded and key in profile.features
    ]


def _make_block(block: str, severities: dict[str, float]) -> PenaltyBlock:
    values = np.asarray(list(severities.values()), dtype=np.float64)
    severity = (
        0.0 if values.size == 0 else float(0.7 * np.max(values) + 0.3 * np.mean(values))
    )
    maximum = BLOCK_MAX_PENALTIES[block]
    return PenaltyBlock(
        key=block,
        max_penalty=maximum,
        severity=severity,
        penalty=maximum * severity,
        feature_severities=severities,
        evidence=tuple(severities),
    )


def _integrity_severities(metric_map: dict[str, Metric]) -> dict[str, float]:
    required = (
        "integrity.true_peak_dbtp",
        "integrity.dc_offset_dbfs",
        "integrity.clipped_sample_ratio",
        "integrity.longest_clipped_run_ms",
    )
    missing = [key for key in required if key not in metric_map]
    if missing:
        raise ProfileError(f"Missing integrity evidence: {', '.join(missing)}")
    true_peak = metric_map[required[0]].value
    dc = metric_map[required[1]].value
    clipped_ratio = metric_map[required[2]].value
    clipped_run = metric_map[required[3]].value
    return {
        required[0]: float(np.clip(true_peak, 0.0, 1.0)),
        required[1]: float(np.clip((dc + 60.0) / 20.0, 0.0, 1.0)),
        required[2]: float(np.clip(clipped_ratio / 0.001, 0.0, 1.0)),
        required[3]: float(np.clip(clipped_run / 20.0, 0.0, 1.0)),
    }


def _findings_for_block(
    block: PenaltyBlock,
    metric_map: dict[str, Metric],
    profile: GenreProfile,
) -> list[Finding]:
    findings: list[Finding] = []
    ordered = sorted(
        block.feature_severities.items(), key=lambda item: item[1], reverse=True
    )
    for key, severity in ordered[:3]:
        if severity <= 0.0:
            continue
        distribution = profile.features[key]
        observed = metric_map[key].value
        findings.append(
            Finding(
                id=f"{block.key}_{key.replace('.', '_')}_outside_profile",
                category=block.key,
                title="Measurement outside the released genre profile",
                description=(
                    f"{key} measured {observed:.3f}; the released profile interval is "
                    f"{distribution.q10:.3f} through {distribution.q90:.3f}."
                ),
                evidence=(key,),
                confidence=metric_map[key].confidence,
                severity=FindingSeverity.WARNING
                if severity >= 0.5
                else FindingSeverity.NOTICE,
                observed_value=observed,
                unit=metric_map[key].unit,
                acceptable_min=distribution.q10,
                acceptable_max=distribution.q90,
                time_ranges=_whole_track_range(metric_map),
            )
        )
    return findings


def _integrity_findings(
    block: PenaltyBlock, metric_map: dict[str, Metric]
) -> list[Finding]:
    titles = {
        "integrity.true_peak_dbtp": "True peak exceeds 0 dBTP",
        "integrity.dc_offset_dbfs": "DC offset exceeds the no-penalty range",
        "integrity.clipped_sample_ratio": "Clipped samples were detected",
        "integrity.longest_clipped_run_ms": "A sustained clipped run was detected",
    }
    acceptable_maxima = {
        "integrity.true_peak_dbtp": 0.0,
        "integrity.dc_offset_dbfs": -60.0,
        "integrity.clipped_sample_ratio": 0.0,
        "integrity.longest_clipped_run_ms": 0.0,
    }
    findings: list[Finding] = []
    for key, severity in block.feature_severities.items():
        if severity <= 0.0:
            continue
        findings.append(
            Finding(
                id=key.replace(".", "_"),
                category="integrity",
                title=titles[key],
                description=f"{key} measured {metric_map[key].value:.3f} {metric_map[key].unit}.",
                evidence=(key,),
                confidence=metric_map[key].confidence,
                severity=FindingSeverity.WARNING
                if severity >= 0.5
                else FindingSeverity.NOTICE,
                observed_value=metric_map[key].value,
                unit=metric_map[key].unit,
                acceptable_max=acceptable_maxima[key],
                time_ranges=_finding_ranges(key, metric_map),
            )
        )
    return findings


def _whole_track_range(metric_map: dict[str, Metric]) -> tuple[TimeRange, ...]:
    duration = metric_map.get("source.duration_seconds")
    if duration is None or duration.value <= 0.0:
        return ()
    return (TimeRange(start_seconds=0.0, end_seconds=duration.value),)


def _finding_ranges(key: str, metric_map: dict[str, Metric]) -> tuple[TimeRange, ...]:
    if key in {"integrity.clipped_sample_ratio", "integrity.longest_clipped_run_ms"}:
        raw_ranges = metric_map[key].parameters.get("clipped_intervals", [])
        ranges = tuple(
            TimeRange(
                start_seconds=float(item["start_seconds"]),
                end_seconds=float(item["end_seconds"]),
            )
            for item in raw_ranges
            if isinstance(item, dict)
            and "start_seconds" in item
            and "end_seconds" in item
        )
        if ranges:
            return ranges
    return _whole_track_range(metric_map)
