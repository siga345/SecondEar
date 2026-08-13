"""Public Mixing analysis orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from .analyzers import (
    SignalIntegrityAnalyzer,
    StereoFieldAnalyzer,
    TonalBalanceAnalyzer,
)
from .audio import AudioData, SoundFileDecoder
from .config import ANALYSIS_VERSION, FORMULA_VERSION, REFERENCE_VERSION
from .elements import ElementBalanceAnalyzer
from .errors import AnalysisError, ProfileError, SeparationError
from .loudness import EbuR128Analyzer
from .models import (
    AnalysisStatus,
    EvidenceType,
    Metric,
    MixingResult,
    PrimaryGenre,
    ReferenceComparison,
    SeparatorIdentity,
)
from .profiles import GenreProfile, ProfileRegistry
from .scoring import MixingScoreEngine
from .separation import DemucsSeparator, SourceSeparator


class MixingPipeline:
    """Reusable synchronous Mixing v1 pipeline with explicit dependencies."""

    def __init__(
        self,
        *,
        decoder: SoundFileDecoder | None = None,
        separator: SourceSeparator | None = None,
        profile_registry: ProfileRegistry | None = None,
        profiles: Mapping[PrimaryGenre, GenreProfile] | None = None,
    ) -> None:
        self.decoder = decoder or SoundFileDecoder()
        self.separator = separator or DemucsSeparator()
        self.profile_registry = profile_registry
        self.profiles = dict(profiles or {})
        self.loudness = EbuR128Analyzer()
        self.integrity = SignalIntegrityAnalyzer()
        self.stereo = StereoFieldAnalyzer()
        self.tonal = TonalBalanceAnalyzer()
        self.elements = ElementBalanceAnalyzer(self.loudness)
        self.scorer = MixingScoreEngine()

    def analyze(
        self,
        audio_path: str | Path,
        primary_genre: PrimaryGenre | str,
        reference_path: str | Path | None = None,
    ) -> MixingResult:
        created_at = datetime.now(UTC).isoformat()
        try:
            genre = PrimaryGenre(primary_genre)
        except ValueError:
            return _empty_result(
                AnalysisStatus.NOT_EVALUATED,
                str(primary_genre),
                created_at,
                "Unsupported primary genre.",
            )

        try:
            target_audio = self.decoder.decode(audio_path)
        except AnalysisError as exc:
            return _empty_result(
                AnalysisStatus.NOT_EVALUATED,
                genre,
                created_at,
                str(exc),
            )

        target_metrics = self._direct_metrics(target_audio)
        separator_identity: SeparatorIdentity | None = None
        limitations: list[str] = [
            "A final stereo master cannot identify whether an observed issue originated in mixing or mastering.",
            "Element balance relies on estimated vocals, drums, bass, and other roles rather than original stems.",
        ]
        try:
            target_stems = self.separator.separate(target_audio)
            separator_identity = target_stems.identity
            target_metrics += self.elements.analyze(target_stems)
        except SeparationError as exc:
            reference = self._reference_comparison(
                reference_path, target_metrics, include_elements=False
            )
            return MixingResult(
                status=AnalysisStatus.INSUFFICIENT_DATA,
                score=None,
                raw_score=None,
                confidence=_minimum_confidence(target_metrics, default=0.0),
                primary_genre=genre,
                analysis_version=ANALYSIS_VERSION,
                formula_version=FORMULA_VERSION,
                profile_version=None,
                created_at=created_at,
                source_sha256=target_audio.content_sha256,
                analyzer_versions=_analyzer_versions(target_metrics),
                metrics=target_metrics,
                limitations=tuple(limitations + [str(exc)]),
                separator=None,
                reference_comparison=reference,
            )

        reference = self._reference_comparison(
            reference_path, target_metrics, include_elements=True
        )
        profile: GenreProfile | None = None
        try:
            profile = self._profile(genre)
            outcome = self.scorer.score(target_metrics, profile, separator_identity)
        except ProfileError as exc:
            return MixingResult(
                status=AnalysisStatus.INSUFFICIENT_DATA,
                score=None,
                raw_score=None,
                confidence=_minimum_confidence(target_metrics, default=0.0),
                primary_genre=genre,
                analysis_version=ANALYSIS_VERSION,
                formula_version=FORMULA_VERSION,
                profile_version=profile.version if profile is not None else None,
                created_at=created_at,
                source_sha256=target_audio.content_sha256,
                analyzer_versions=_analyzer_versions(target_metrics),
                metrics=target_metrics,
                limitations=tuple(limitations + [str(exc)]),
                separator=separator_identity,
                reference_comparison=reference,
            )

        return MixingResult(
            status=AnalysisStatus.EVALUATED,
            score=outcome.score,
            raw_score=outcome.raw_score,
            confidence=outcome.confidence,
            primary_genre=genre,
            analysis_version=ANALYSIS_VERSION,
            formula_version=FORMULA_VERSION,
            profile_version=profile.version,
            created_at=created_at,
            source_sha256=target_audio.content_sha256,
            analyzer_versions=_analyzer_versions(target_metrics),
            metrics=target_metrics,
            penalty_blocks=outcome.blocks,
            findings=outcome.findings,
            limitations=tuple(limitations),
            separator=separator_identity,
            reference_comparison=reference,
        )

    def _direct_metrics(self, audio: AudioData) -> tuple[Metric, ...]:
        return (
            self._source_metrics(audio)
            + self.loudness.analyze(audio).metrics
            + self.integrity.analyze(audio)
            + self.stereo.analyze(audio)
            + self.tonal.analyze(audio)
        )

    def _source_metrics(self, audio: AudioData) -> tuple[Metric, ...]:
        values = (
            ("source.duration_seconds", audio.duration_seconds, "seconds"),
            ("source.sample_rate_hz", float(audio.sample_rate), "Hz"),
            ("source.channel_count", float(audio.channels), "channels"),
        )
        return tuple(
            Metric(
                key=key,
                value=value,
                unit=unit,
                evidence_type=EvidenceType.MEASURED,
                confidence=1.0,
                analyzer="decoder",
                analyzer_version=audio.decoder_version,
                parameters={"format": audio.source_format, "subtype": audio.subtype},
            )
            for key, value, unit in values
        )

    def _profile(self, genre: PrimaryGenre) -> GenreProfile:
        if genre in self.profiles:
            profile = self.profiles[genre]
            if profile.status != "released":
                raise ProfileError("The selected genre profile is not released.")
            return profile
        if self.profile_registry is None:
            raise ProfileError(
                "No released lossless genre profile is configured; raw measurements are available."
            )
        return self.profile_registry.get(genre)

    def _reference_comparison(
        self,
        reference_path: str | Path | None,
        target_metrics: tuple[Metric, ...],
        *,
        include_elements: bool,
    ) -> ReferenceComparison | None:
        if reference_path is None:
            return None
        limitations = ["Reference differences never change the target Mixing score."]
        try:
            audio = self.decoder.decode(reference_path)
            reference_metrics = self._direct_metrics(audio)
            if include_elements:
                reference_stems = self.separator.separate(audio)
                reference_metrics += self.elements.analyze(reference_stems)
            deltas = _metric_deltas(target_metrics, reference_metrics)
            return ReferenceComparison(
                status=AnalysisStatus.EVALUATED,
                analyzer_version=REFERENCE_VERSION,
                metric_deltas=deltas,
                limitations=tuple(limitations),
            )
        except AnalysisError as exc:
            return ReferenceComparison(
                status=AnalysisStatus.NOT_EVALUATED,
                analyzer_version=REFERENCE_VERSION,
                limitations=tuple(limitations + [str(exc)]),
            )


def analyze_mixing(
    audio_path: str | Path,
    primary_genre: PrimaryGenre | str,
    reference_path: str | Path | None = None,
    *,
    profiles_path: str | Path | None = None,
    separator: SourceSeparator | None = None,
) -> MixingResult:
    """Analyze one lossless stereo master with an optional comparison reference.

    Public scoring requires a released genre profile. Without one, or without a
    reliable source separator, the function returns all defensible measurements
    and an explicit ``insufficient_data`` status rather than fabricating a score.
    """

    registry = ProfileRegistry(profiles_path) if profiles_path is not None else None
    return MixingPipeline(separator=separator, profile_registry=registry).analyze(
        audio_path, primary_genre, reference_path
    )


def _metric_deltas(
    target: tuple[Metric, ...], reference: tuple[Metric, ...]
) -> dict[str, float]:
    target_values = {metric.key: metric.value for metric in target}
    reference_values = {metric.key: metric.value for metric in reference}
    return {
        key: target_values[key] - reference_values[key]
        for key in sorted(target_values.keys() & reference_values.keys())
    }


def _minimum_confidence(metrics: tuple[Metric, ...], *, default: float) -> float:
    return min((metric.confidence for metric in metrics), default=default)


def _analyzer_versions(metrics: tuple[Metric, ...]) -> dict[str, str]:
    return {
        metric.analyzer: metric.analyzer_version
        for metric in sorted(
            metrics, key=lambda item: (item.analyzer, item.analyzer_version)
        )
    }


def _empty_result(
    status: AnalysisStatus,
    genre: PrimaryGenre | str,
    created_at: str,
    limitation: str,
) -> MixingResult:
    return MixingResult(
        status=status,
        score=None,
        raw_score=None,
        confidence=0.0,
        primary_genre=genre,
        analysis_version=ANALYSIS_VERSION,
        formula_version=FORMULA_VERSION,
        profile_version=None,
        created_at=created_at,
        source_sha256=None,
        limitations=(limitation,),
    )
