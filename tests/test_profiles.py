from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
from secondear_analysis.config import ANALYSIS_VERSION, FORMULA_VERSION
from secondear_analysis.errors import ProfileError
from secondear_analysis.models import PrimaryGenre
from secondear_analysis.profiles import (
    GenreProfile,
    ProfileObservation,
    ProfileReleaseEvidence,
    build_genre_profile,
)

from .helpers import SEPARATOR_IDENTITY


def _observations(count: int = 50) -> list[ProfileObservation]:
    items: list[ProfileObservation] = []
    for index in range(count):
        if index < 30:
            split = "calibration"
        elif index < 40:
            split = "validation"
        else:
            split = "holdout"
        items.append(
            ProfileObservation(
                track_id=f"track-{index}",
                artist_id=f"artist-{index // 2}",
                genre=PrimaryGenre.RAP,
                substyle=f"substyle-{index % 4}",
                period=f"period-{index % 4}",
                split=split,
                rights_confirmed=True,
                source_format="WAV" if index % 2 == 0 else "FLAC",
                audio_sha256=f"{index:064x}",
                analysis_version=ANALYSIS_VERSION,
                formula_version=FORMULA_VERSION,
                analyzer_versions={"fixture": "1.0.0"},
                metrics={"tonal.erb_00_relative_db": float(index)},
                separator=SEPARATOR_IDENTITY,
            )
        )
    return items


def _passed() -> ProfileReleaseEvidence:
    return ProfileReleaseEvidence(True, True, True)


def test_builds_released_profile_from_30_10_10_lossless_corpus() -> None:
    profile = build_genre_profile(
        _observations(),
        version="rap-mixing-0.1.0",
        release_evidence=_passed(),
        release=True,
    )

    assert profile.status == "released"
    assert profile.source_count == 50
    assert profile.split_counts == {"calibration": 30, "validation": 10, "holdout": 10}
    assert profile.corpus_summary == {
        "artist_count": 25,
        "substyle_count": 4,
        "period_count": 4,
    }
    distribution = profile.features["tonal.erb_00_relative_db"]
    assert distribution.sample_count == 30
    assert distribution.q10 < distribution.median < distribution.q90


def test_profile_json_round_trip_preserves_versions_and_corpus_summary(
    tmp_path: Path,
) -> None:
    profile = build_genre_profile(
        _observations(),
        version="rap-mixing-0.1.0",
        release_evidence=_passed(),
        release=True,
    )
    path = tmp_path / "rap.json"

    profile.save(path)

    assert GenreProfile.load(path) == profile


def test_release_rejects_insufficient_corpus() -> None:
    with pytest.raises(ProfileError, match="30/10/10"):
        build_genre_profile(
            _observations(49),
            version="rap-mixing-0.1.0",
            release_evidence=_passed(),
            release=True,
        )


def test_release_rejects_unconfirmed_rights() -> None:
    observations = _observations()
    observations[0] = replace(observations[0], rights_confirmed=False)

    with pytest.raises(ProfileError, match="confirmed analysis rights"):
        build_genre_profile(
            observations,
            version="rap-mixing-0.1.0",
            release_evidence=_passed(),
            release=True,
        )


def test_observation_schema_does_not_coerce_rights_strings() -> None:
    data = _observations(1)[0].to_dict()
    data["rights_confirmed"] = "false"

    with pytest.raises(ProfileError, match="invalid schema"):
        ProfileObservation.from_dict(data)


def test_release_rejects_lossy_observation() -> None:
    observations = _observations()
    observations[0] = replace(observations[0], source_format="MP3")

    with pytest.raises(ProfileError, match="lossless"):
        build_genre_profile(
            observations,
            version="rap-mixing-0.1.0",
            release_evidence=_passed(),
            release=True,
        )


def test_release_requires_all_validation_evidence() -> None:
    with pytest.raises(ProfileError, match="evidence must pass"):
        build_genre_profile(
            _observations(),
            version="rap-mixing-0.1.0",
            release_evidence=ProfileReleaseEvidence(True, True, False),
            release=True,
        )


def test_release_rejects_more_than_two_tracks_per_artist() -> None:
    observations = _observations()
    observations[2] = replace(observations[2], artist_id=observations[0].artist_id)

    with pytest.raises(ProfileError, match="at most two"):
        build_genre_profile(
            observations,
            version="rap-mixing-0.1.0",
            release_evidence=_passed(),
            release=True,
        )


def test_release_requires_multiple_substyles_and_periods() -> None:
    observations = [
        replace(item, substyle="same", period="same") for item in _observations()
    ]

    with pytest.raises(ProfileError, match="substyle and period"):
        build_genre_profile(
            observations,
            version="rap-mixing-0.1.0",
            release_evidence=_passed(),
            release=True,
        )


def test_profile_rejects_mixed_analyzer_versions() -> None:
    observations = _observations()
    observations[0] = replace(
        observations[0], analyzer_versions={"fixture": "different"}
    )

    with pytest.raises(ProfileError, match="same analyzer versions"):
        build_genre_profile(
            observations,
            version="rap-mixing-0.1.0",
            release_evidence=_passed(),
        )
