"""Typed domain models for explainable Mixing analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class AnalysisStatus(StrEnum):
    EVALUATED = "evaluated"
    INSUFFICIENT_DATA = "insufficient_data"
    NOT_EVALUATED = "not_evaluated"


class EvidenceType(StrEnum):
    MEASURED = "measured"
    ESTIMATED = "estimated"
    DERIVED = "derived"
    BENCHMARKED = "benchmarked"


class FindingSeverity(StrEnum):
    INFO = "info"
    NOTICE = "notice"
    WARNING = "warning"


class PrimaryGenre(StrEnum):
    RAP = "rap"
    POP = "pop"
    R_AND_B = "r_and_b"
    ROCK = "rock"
    COUNTRY = "country"
    ELECTRONIC = "electronic"


@dataclass(frozen=True, slots=True)
class TimeRange:
    start_seconds: float
    end_seconds: float


@dataclass(frozen=True, slots=True)
class Metric:
    key: str
    value: float
    unit: str | None
    evidence_type: EvidenceType
    confidence: float
    analyzer: str
    analyzer_version: str
    parameters: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Finding:
    id: str
    category: str
    title: str
    description: str
    evidence: tuple[str, ...]
    confidence: float
    severity: FindingSeverity
    observed_value: float | None = None
    unit: str | None = None
    acceptable_min: float | None = None
    acceptable_max: float | None = None
    time_ranges: tuple[TimeRange, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PenaltyBlock:
    key: str
    max_penalty: float
    severity: float
    penalty: float
    feature_severities: dict[str, float]
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SeparatorIdentity:
    implementation: str
    implementation_version: str
    model: str
    model_checksum: str
    torch_version: str = "not_recorded"
    torchaudio_version: str = "not_recorded"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ReferenceComparison:
    status: AnalysisStatus
    analyzer_version: str
    metric_deltas: dict[str, float] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MixingResult:
    status: AnalysisStatus
    score: int | None
    raw_score: float | None
    confidence: float
    primary_genre: PrimaryGenre | str
    analysis_version: str
    formula_version: str
    profile_version: str | None
    created_at: str
    source_sha256: str | None
    analyzer_versions: dict[str, str] = field(default_factory=dict)
    metrics: tuple[Metric, ...] = ()
    penalty_blocks: tuple[PenaltyBlock, ...] = ()
    findings: tuple[Finding, ...] = ()
    limitations: tuple[str, ...] = ()
    separator: SeparatorIdentity | None = None
    reference_comparison: ReferenceComparison | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        data["primary_genre"] = (
            self.primary_genre.value
            if isinstance(self.primary_genre, PrimaryGenre)
            else self.primary_genre
        )
        for metric in data["metrics"]:
            metric["evidence_type"] = metric["evidence_type"].value
        for finding in data["findings"]:
            finding["severity"] = finding["severity"].value
        if self.reference_comparison is not None:
            data["reference_comparison"]["status"] = (
                self.reference_comparison.status.value
            )
        return data
