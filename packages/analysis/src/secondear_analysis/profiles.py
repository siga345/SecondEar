"""Versioned genre profiles and lawful-corpus release gates."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np

from .config import (
    ANALYSIS_VERSION,
    FORMULA_VERSION,
    PROFILE_REQUIREMENTS,
    SUPPORTED_FORMATS,
)
from .errors import ProfileError
from .models import PrimaryGenre, SeparatorIdentity

ProfileStatus = Literal["draft", "released"]
CorpusSplit = Literal["calibration", "validation", "holdout"]


@dataclass(frozen=True, slots=True)
class FeatureDistribution:
    median: float
    q10: float
    q90: float
    mad: float
    sample_count: int

    @property
    def robust_scale(self) -> float:
        quantile_scale = max(0.0, self.q90 - self.q10) / 2.563
        return max(1.4826 * self.mad, quantile_scale, 1e-6)

    def severity(self, value: float) -> float:
        """Return zero inside Q10-Q90 and a capped robust outside distance."""

        if self.q10 <= value <= self.q90:
            return 0.0
        distance = self.q10 - value if value < self.q10 else value - self.q90
        return float(np.clip(distance / (2.0 * self.robust_scale), 0.0, 1.0))


@dataclass(frozen=True, slots=True)
class GenreProfile:
    genre: PrimaryGenre
    version: str
    status: ProfileStatus
    analysis_version: str
    formula_version: str
    source_count: int
    split_counts: dict[str, int]
    separator: SeparatorIdentity
    features: dict[str, FeatureDistribution]
    analyzer_versions: dict[str, str]
    corpus_summary: dict[str, int]
    validation_evidence: dict[str, bool]

    @property
    def confidence(self) -> float:
        return 0.90 if self.status == "released" else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "genre": self.genre.value,
            "version": self.version,
            "status": self.status,
            "analysis_version": self.analysis_version,
            "formula_version": self.formula_version,
            "source_count": self.source_count,
            "split_counts": self.split_counts,
            "separator": self.separator.to_dict(),
            "features": {key: asdict(value) for key, value in self.features.items()},
            "analyzer_versions": self.analyzer_versions,
            "corpus_summary": self.corpus_summary,
            "validation_evidence": self.validation_evidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GenreProfile:
        try:
            return cls(
                genre=PrimaryGenre(data["genre"]),
                version=str(data["version"]),
                status=data["status"],
                analysis_version=str(data["analysis_version"]),
                formula_version=str(data["formula_version"]),
                source_count=int(data["source_count"]),
                split_counts={
                    str(key): int(value) for key, value in data["split_counts"].items()
                },
                separator=SeparatorIdentity(**data["separator"]),
                features={
                    str(key): FeatureDistribution(**value)
                    for key, value in data["features"].items()
                },
                analyzer_versions={
                    str(key): str(value)
                    for key, value in data["analyzer_versions"].items()
                },
                corpus_summary={
                    str(key): int(value)
                    for key, value in data["corpus_summary"].items()
                },
                validation_evidence={
                    str(key): bool(value)
                    for key, value in data["validation_evidence"].items()
                },
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProfileError("The genre profile schema is invalid.") from exc

    @classmethod
    def load(cls, path: str | Path) -> GenreProfile:
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ProfileError("The genre profile could not be read.") from exc
        if not isinstance(data, dict):
            raise ProfileError("The genre profile root must be an object.")
        return cls.from_dict(data)

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


@dataclass(frozen=True, slots=True)
class ProfileObservation:
    track_id: str
    artist_id: str
    genre: PrimaryGenre
    substyle: str
    period: str
    split: CorpusSplit
    rights_confirmed: bool
    source_format: str
    audio_sha256: str
    analysis_version: str
    formula_version: str
    analyzer_versions: dict[str, str]
    metrics: dict[str, float]
    separator: SeparatorIdentity

    def to_dict(self) -> dict[str, Any]:
        return {
            "track_id": self.track_id,
            "artist_id": self.artist_id,
            "genre": self.genre.value,
            "substyle": self.substyle,
            "period": self.period,
            "split": self.split,
            "rights_confirmed": self.rights_confirmed,
            "source_format": self.source_format,
            "audio_sha256": self.audio_sha256,
            "analysis_version": self.analysis_version,
            "formula_version": self.formula_version,
            "analyzer_versions": self.analyzer_versions,
            "metrics": self.metrics,
            "separator": self.separator.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProfileObservation:
        try:
            rights_confirmed = data["rights_confirmed"]
            if not isinstance(rights_confirmed, bool):
                raise TypeError("rights_confirmed must be a boolean")
            return cls(
                track_id=str(data["track_id"]),
                artist_id=str(data["artist_id"]),
                genre=PrimaryGenre(data["genre"]),
                substyle=str(data["substyle"]),
                period=str(data["period"]),
                split=data["split"],
                rights_confirmed=rights_confirmed,
                source_format=str(data["source_format"]).upper(),
                audio_sha256=str(data["audio_sha256"]),
                analysis_version=str(data["analysis_version"]),
                formula_version=str(data["formula_version"]),
                analyzer_versions={
                    str(key): str(value)
                    for key, value in data["analyzer_versions"].items()
                },
                metrics={
                    str(key): float(value) for key, value in data["metrics"].items()
                },
                separator=SeparatorIdentity(**data["separator"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProfileError("A profile observation has an invalid schema.") from exc


@dataclass(frozen=True, slots=True)
class ProfileReleaseEvidence:
    ebu_passed: bool
    validation_passed: bool
    holdout_passed: bool

    @property
    def complete(self) -> bool:
        return self.ebu_passed and self.validation_passed and self.holdout_passed


class ProfileRegistry:
    """Load one released JSON profile per primary genre."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)

    def get(self, genre: PrimaryGenre) -> GenreProfile:
        profile = GenreProfile.load(self.directory / f"{genre.value}.json")
        if profile.genre != genre:
            raise ProfileError("The profile genre does not match its registry key.")
        if profile.status != "released":
            raise ProfileError("The selected genre profile is not released.")
        if profile.analysis_version != ANALYSIS_VERSION:
            raise ProfileError(
                "The selected genre profile uses a different analysis pipeline."
            )
        if profile.formula_version != FORMULA_VERSION:
            raise ProfileError(
                "The selected genre profile uses a different score formula."
            )
        return profile


def build_genre_profile(
    observations: list[ProfileObservation],
    *,
    version: str,
    release_evidence: ProfileReleaseEvidence,
    release: bool = False,
) -> GenreProfile:
    """Build robust calibration distributions and enforce public release gates."""

    if not observations:
        raise ProfileError("A genre profile requires corpus observations.")
    genres = {observation.genre for observation in observations}
    if len(genres) != 1:
        raise ProfileError("A genre profile cannot combine primary genres.")
    separators = {observation.separator for observation in observations}
    if len(separators) != 1:
        raise ProfileError(
            "All profile observations must use the same separator identity."
        )
    if {observation.analysis_version for observation in observations} != {
        ANALYSIS_VERSION
    }:
        raise ProfileError(
            "All profile observations must use the current analysis version."
        )
    if {observation.formula_version for observation in observations} != {
        FORMULA_VERSION
    }:
        raise ProfileError(
            "All profile observations must use the current formula version."
        )
    analyzer_version_sets = {
        tuple(sorted(observation.analyzer_versions.items()))
        for observation in observations
    }
    if any(not observation.analyzer_versions for observation in observations):
        raise ProfileError("Every profile observation requires analyzer versions.")
    if len(analyzer_version_sets) != 1:
        raise ProfileError(
            "All profile observations must use the same analyzer versions."
        )
    if any(not observation.rights_confirmed for observation in observations):
        raise ProfileError(
            "Every profile observation requires confirmed analysis rights."
        )
    if any(
        observation.source_format not in SUPPORTED_FORMATS
        for observation in observations
    ):
        raise ProfileError(
            "Released profiles may contain only lossless WAV/FLAC observations."
        )
    if len({observation.track_id for observation in observations}) != len(observations):
        raise ProfileError("Track identifiers must be unique within a profile corpus.")
    if len({observation.audio_sha256 for observation in observations}) != len(
        observations
    ):
        raise ProfileError("Audio hashes must be unique within a profile corpus.")
    if any(
        not observation.substyle.strip() or not observation.period.strip()
        for observation in observations
    ):
        raise ProfileError(
            "Every profile observation requires substyle and period provenance."
        )

    artist_counts: dict[str, int] = {}
    split_counts = {"calibration": 0, "validation": 0, "holdout": 0}
    for observation in observations:
        if observation.split not in split_counts:
            raise ProfileError(
                "Corpus split must be calibration, validation, or holdout."
            )
        split_counts[observation.split] += 1
        artist_counts[observation.artist_id] = (
            artist_counts.get(observation.artist_id, 0) + 1
        )
    if max(artist_counts.values()) > PROFILE_REQUIREMENTS.max_tracks_per_artist:
        raise ProfileError("A profile may contain at most two tracks per artist.")

    required = PROFILE_REQUIREMENTS
    counts_ready = (
        len(observations) >= required.total
        and split_counts["calibration"] >= required.calibration
        and split_counts["validation"] >= required.validation
        and split_counts["holdout"] >= required.holdout
    )
    if release and not counts_ready:
        raise ProfileError(
            "The corpus does not satisfy the 30/10/10 lossless release gate."
        )
    substyles = {observation.substyle for observation in observations}
    periods = {observation.period for observation in observations}
    if release and (len(substyles) < 2 or len(periods) < 2):
        raise ProfileError(
            "A released profile requires more than one represented substyle and period."
        )
    if release and not release_evidence.complete:
        raise ProfileError(
            "EBU, validation, and holdout evidence must pass before release."
        )

    calibration = [item for item in observations if item.split == "calibration"]
    feature_keys = sorted({key for item in calibration for key in item.metrics})
    distributions: dict[str, FeatureDistribution] = {}
    for key in feature_keys:
        values = np.asarray(
            [item.metrics[key] for item in calibration if key in item.metrics],
            dtype=np.float64,
        )
        values = values[np.isfinite(values)]
        if values.size < 10:
            continue
        median = float(np.median(values))
        distributions[key] = FeatureDistribution(
            median=median,
            q10=float(np.percentile(values, 10)),
            q90=float(np.percentile(values, 90)),
            mad=float(np.median(np.abs(values - median))),
            sample_count=int(values.size),
        )
    if not distributions:
        raise ProfileError(
            "Calibration observations contain no usable numerical features."
        )

    return GenreProfile(
        genre=next(iter(genres)),
        version=version,
        status="released" if release else "draft",
        analysis_version=ANALYSIS_VERSION,
        formula_version=FORMULA_VERSION,
        source_count=len(observations),
        split_counts=split_counts,
        separator=next(iter(separators)),
        features=distributions,
        analyzer_versions=dict(analyzer_version_sets.pop()),
        corpus_summary={
            "artist_count": len(artist_counts),
            "substyle_count": len(substyles),
            "period_count": len(periods),
        },
        validation_evidence={
            "ebu_passed": release_evidence.ebu_passed,
            "validation_passed": release_evidence.validation_passed,
            "holdout_passed": release_evidence.holdout_passed,
        },
    )


def load_observations(path: str | Path) -> list[ProfileObservation]:
    observations: list[ProfileObservation] = []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ProfileError("The observation manifest could not be read.") from exc
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ProfileError(
                f"Invalid JSON on observation line {line_number}."
            ) from exc
        if not isinstance(value, dict):
            raise ProfileError(f"Observation line {line_number} must be an object.")
        observations.append(ProfileObservation.from_dict(value))
    return observations
