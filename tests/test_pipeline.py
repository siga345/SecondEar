from __future__ import annotations

import json
from pathlib import Path

import pytest
from secondear_analysis.errors import SeparationError
from secondear_analysis.models import AnalysisStatus, PrimaryGenre
from secondear_analysis.pipeline import MixingPipeline

from .helpers import FakeSeparator, released_profile


class FailingSeparator:
    def separate(self, audio):
        raise SeparationError("Fixture separation failure.")


@pytest.mark.integration
def test_pipeline_returns_measurements_but_no_score_without_profile(
    stereo_wav: Path,
) -> None:
    result = MixingPipeline(separator=FakeSeparator()).analyze(stereo_wav, "rap")

    assert result.status is AnalysisStatus.INSUFFICIENT_DATA
    assert result.score is None
    assert result.raw_score is None
    assert result.separator is not None
    assert result.analyzer_versions["loudness"] == "libebur128-meter-0.1.0"
    assert len(result.metrics) > 50
    assert any(
        "No released lossless genre profile" in item for item in result.limitations
    )


@pytest.mark.integration
def test_pipeline_scores_with_released_profile_and_reference_does_not_change_score(
    stereo_wav: Path,
) -> None:
    separator = FakeSeparator()
    unprofiled = MixingPipeline(separator=separator).analyze(
        stereo_wav, PrimaryGenre.RAP
    )
    profile = released_profile(unprofiled.metrics)
    pipeline = MixingPipeline(separator=separator, profiles={PrimaryGenre.RAP: profile})

    without_reference = pipeline.analyze(stereo_wav, PrimaryGenre.RAP)
    with_reference = pipeline.analyze(stereo_wav, PrimaryGenre.RAP, stereo_wav)

    assert without_reference.status is AnalysisStatus.EVALUATED
    assert without_reference.score == 10
    assert with_reference.score == without_reference.score
    assert with_reference.raw_score == without_reference.raw_score
    assert with_reference.reference_comparison is not None
    assert with_reference.reference_comparison.status is AnalysisStatus.EVALUATED
    assert all(
        value == pytest.approx(0.0)
        for value in with_reference.reference_comparison.metric_deltas.values()
    )


@pytest.mark.integration
def test_absent_stem_is_not_penalized_as_bad_balance(stereo_wav: Path) -> None:
    separator = FakeSeparator(absent=("vocals",))
    unprofiled = MixingPipeline(separator=separator).analyze(
        stereo_wav, PrimaryGenre.ROCK
    )
    keys = {metric.key for metric in unprofiled.metrics}
    assert "element.vocals_relative_lufs" not in keys
    profile = released_profile(unprofiled.metrics, genre=PrimaryGenre.ROCK)

    result = MixingPipeline(
        separator=separator, profiles={PrimaryGenre.ROCK: profile}
    ).analyze(stereo_wav, PrimaryGenre.ROCK)

    assert result.status is AnalysisStatus.EVALUATED
    assert result.score == 10


@pytest.mark.integration
def test_single_active_role_does_not_invent_masking_evidence(stereo_wav: Path) -> None:
    separator = FakeSeparator(absent=("vocals", "drums", "bass"))
    result = MixingPipeline(separator=separator).analyze(
        stereo_wav, PrimaryGenre.ELECTRONIC
    )
    keys = {metric.key for metric in result.metrics}

    assert "element.other_relative_lufs" in keys
    assert "element.other_mask_margin_median_db" not in keys


@pytest.mark.integration
def test_separator_failure_declines_score_but_keeps_direct_metrics(
    stereo_wav: Path,
) -> None:
    result = MixingPipeline(separator=FailingSeparator()).analyze(
        stereo_wav, PrimaryGenre.POP
    )

    assert result.status is AnalysisStatus.INSUFFICIENT_DATA
    assert result.score is None
    assert result.separator is None
    assert any(metric.key == "dynamics.integrated_lufs" for metric in result.metrics)
    assert any("Fixture separation failure" in item for item in result.limitations)


def test_unsupported_genre_returns_not_evaluated_without_false_genre() -> None:
    result = MixingPipeline(separator=FailingSeparator()).analyze("missing.wav", "jazz")

    assert result.status is AnalysisStatus.NOT_EVALUATED
    assert result.primary_genre == "jazz"
    assert result.source_sha256 is None


@pytest.mark.integration
def test_result_is_json_serializable(stereo_wav: Path) -> None:
    result = MixingPipeline(separator=FailingSeparator()).analyze(stereo_wav, "country")
    serialized = json.dumps(result.to_dict(), sort_keys=True)
    assert '"status": "insufficient_data"' in serialized
    assert '"primary_genre": "country"' in serialized


@pytest.mark.integration
def test_raw_metrics_and_score_are_reproducible(stereo_wav: Path) -> None:
    separator = FakeSeparator()
    raw = MixingPipeline(separator=separator).analyze(stereo_wav, PrimaryGenre.RAP)
    profile = released_profile(raw.metrics)
    pipeline = MixingPipeline(separator=separator, profiles={PrimaryGenre.RAP: profile})

    first = pipeline.analyze(stereo_wav, PrimaryGenre.RAP)
    second = pipeline.analyze(stereo_wav, PrimaryGenre.RAP)

    assert first.metrics == second.metrics
    assert first.raw_score == second.raw_score
    assert first.score == second.score
