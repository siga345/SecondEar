from __future__ import annotations

from dataclasses import replace

import pytest
from secondear_analysis.errors import ProfileError
from secondear_analysis.profiles import FeatureDistribution
from secondear_analysis.scoring import MixingScoreEngine

from .helpers import SEPARATOR_IDENTITY, metric, released_profile, scoring_metrics


def test_clean_in_profile_evidence_scores_ten() -> None:
    metrics = scoring_metrics()
    outcome = MixingScoreEngine().score(
        metrics, released_profile(metrics, half_width=1.0), SEPARATOR_IDENTITY
    )

    assert outcome.raw_score == pytest.approx(10.0)
    assert outcome.score == 10
    assert outcome.confidence == pytest.approx(0.9)


def test_integrity_penalty_is_monotonic() -> None:
    clean = scoring_metrics()
    medium = scoring_metrics(
        **{
            "integrity.true_peak_dbtp": 0.5,
            "integrity.clipped_sample_ratio": 0.0002,
            "integrity.longest_clipped_run_ms": 2.0,
        }
    )
    severe = scoring_metrics(
        **{
            "integrity.true_peak_dbtp": 1.0,
            "integrity.dc_offset_dbfs": -40.0,
            "integrity.clipped_sample_ratio": 0.001,
            "integrity.longest_clipped_run_ms": 20.0,
        }
    )
    profile = released_profile(clean, half_width=1.0)
    engine = MixingScoreEngine()

    clean_score = engine.score(clean, profile, SEPARATOR_IDENTITY).raw_score
    medium_score = engine.score(medium, profile, SEPARATOR_IDENTITY).raw_score
    severe_score = engine.score(severe, profile, SEPARATOR_IDENTITY).raw_score

    assert clean_score > medium_score > severe_score
    assert severe_score == pytest.approx(8.0)


def test_findings_expose_observed_range_and_track_interval() -> None:
    metrics = scoring_metrics(**{"integrity.true_peak_dbtp": 0.5}) + (
        metric("source.duration_seconds", 120.0, confidence=1.0),
    )
    profile = released_profile(scoring_metrics(), half_width=1.0)

    outcome = MixingScoreEngine().score(metrics, profile, SEPARATOR_IDENTITY)
    finding = next(
        item for item in outcome.findings if item.id == "integrity_true_peak_dbtp"
    )

    assert finding.observed_value == pytest.approx(0.5)
    assert finding.unit is None
    assert finding.acceptable_max == pytest.approx(0.0)
    assert finding.time_ranges[0].start_seconds == pytest.approx(0.0)
    assert finding.time_ranges[0].end_seconds == pytest.approx(120.0)


def test_element_balance_has_greater_penalty_capacity_than_stereo() -> None:
    metrics = scoring_metrics()
    profile = released_profile(metrics, half_width=1.0)
    distributions = dict(profile.features)
    narrow = FeatureDistribution(
        median=0.0, q10=-1.0, q90=1.0, mad=1.0, sample_count=30
    )
    distributions["element.drums_relative_lufs"] = narrow
    distributions["stereo.feature_0"] = narrow
    profile = replace(profile, features=distributions)
    engine = MixingScoreEngine()

    element_outlier = tuple(
        replace(item, value=10.0) if item.key == "element.drums_relative_lufs" else item
        for item in metrics
    )
    stereo_outlier = tuple(
        replace(item, value=10.0) if item.key == "stereo.feature_0" else item
        for item in metrics
    )

    element_score = engine.score(element_outlier, profile, SEPARATOR_IDENTITY).raw_score
    stereo_score = engine.score(stereo_outlier, profile, SEPARATOR_IDENTITY).raw_score
    assert element_score < stereo_score


@pytest.mark.parametrize(
    ("feature_key", "block_key"),
    [
        ("element.drums_relative_lufs", "element_balance"),
        ("stereo.feature_0", "stereo"),
        ("tonal.erb_00_relative_db", "tonal"),
        ("dynamics.feature_0", "dynamics"),
    ],
)
def test_stronger_profile_deformation_never_reduces_its_penalty(
    feature_key: str, block_key: str
) -> None:
    baseline = scoring_metrics()
    profile = released_profile(baseline, half_width=1.0)
    engine = MixingScoreEngine()

    medium = tuple(
        replace(item, value=3.0) if item.key == feature_key else item
        for item in baseline
    )
    severe = tuple(
        replace(item, value=10.0) if item.key == feature_key else item
        for item in baseline
    )
    medium_outcome = engine.score(medium, profile, SEPARATOR_IDENTITY)
    severe_outcome = engine.score(severe, profile, SEPARATOR_IDENTITY)
    medium_block = next(item for item in medium_outcome.blocks if item.key == block_key)
    severe_block = next(item for item in severe_outcome.blocks if item.key == block_key)

    assert severe_block.penalty >= medium_block.penalty > 0.0
    assert severe_outcome.raw_score <= medium_outcome.raw_score


def test_display_score_uses_half_up_rounding() -> None:
    metrics = scoring_metrics()
    profile = released_profile(metrics, half_width=1.0)
    distributions = dict(profile.features)
    distributions["element.drums_relative_lufs"] = FeatureDistribution(
        median=0.0, q10=-1.0, q90=1.0, mad=1.0, sample_count=30
    )
    distributions["element.bass_relative_lufs"] = distributions[
        "element.drums_relative_lufs"
    ]
    profile = replace(profile, features=distributions)
    robust_scale = distributions["element.drums_relative_lufs"].robust_scale
    outlier_value = 1.0 + 2.0 * robust_scale * 0.625
    outlier = tuple(
        replace(item, value=outlier_value) if item.key.startswith("element.") else item
        for item in metrics
    )

    outcome = MixingScoreEngine().score(outlier, profile, SEPARATOR_IDENTITY)
    assert outcome.raw_score == pytest.approx(7.5)
    assert outcome.score == 8


def test_score_rejects_separator_identity_mismatch() -> None:
    metrics = scoring_metrics()
    profile = released_profile(metrics)
    other = replace(SEPARATOR_IDENTITY, model_checksum="different")

    with pytest.raises(ProfileError, match="separator identities"):
        MixingScoreEngine().score(metrics, profile, other)


def test_score_rejects_analyzer_version_mismatch() -> None:
    metrics = scoring_metrics()
    profile = replace(
        released_profile(metrics), analyzer_versions={"fixture": "different"}
    )

    with pytest.raises(ProfileError, match="analyzer versions"):
        MixingScoreEngine().score(metrics, profile, SEPARATOR_IDENTITY)


def test_score_is_withheld_below_confidence_threshold() -> None:
    metrics = tuple(replace(item, confidence=0.60) for item in scoring_metrics())

    with pytest.raises(ProfileError, match="confidence threshold"):
        MixingScoreEngine().score(
            metrics, released_profile(metrics), SEPARATOR_IDENTITY
        )


def test_absolute_loudness_shift_does_not_change_score_with_headroom() -> None:
    absolute_keys = {
        "dynamics.integrated_lufs",
        "dynamics.short_term_p10_lufs",
        "dynamics.short_term_p50_lufs",
        "dynamics.short_term_p90_lufs",
    }
    metrics = scoring_metrics() + tuple(metric(key, -14.0) for key in absolute_keys)
    shifted = tuple(
        replace(item, value=item.value - 6.0) if item.key in absolute_keys else item
        for item in metrics
    )
    profile = released_profile(metrics, half_width=0.1)
    engine = MixingScoreEngine()

    original = engine.score(metrics, profile, SEPARATOR_IDENTITY)
    quieter = engine.score(shifted, profile, SEPARATOR_IDENTITY)

    assert quieter.raw_score == original.raw_score
    assert quieter.score == original.score
