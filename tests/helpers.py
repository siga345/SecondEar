from __future__ import annotations

import numpy as np
from secondear_analysis.audio import AudioData
from secondear_analysis.config import ANALYSIS_VERSION, FORMULA_VERSION, STEM_NAMES
from secondear_analysis.models import (
    EvidenceType,
    Metric,
    PrimaryGenre,
    SeparatorIdentity,
)
from secondear_analysis.profiles import FeatureDistribution, GenreProfile
from secondear_analysis.separation import StemSet

SEPARATOR_IDENTITY = SeparatorIdentity(
    implementation="test-separator",
    implementation_version="1.0.0",
    model="four-role-fixture",
    model_checksum="fixture-checksum",
)


class FakeSeparator:
    def __init__(self, *, absent: tuple[str, ...] = ()) -> None:
        self.absent = absent

    def separate(self, audio: AudioData) -> StemSet:
        active = [name for name in STEM_NAMES if name not in self.absent]
        sources = {
            name: (
                np.zeros_like(audio.samples)
                if name in self.absent
                else np.ascontiguousarray(audio.samples / len(active), dtype=np.float32)
            )
            for name in STEM_NAMES
        }
        return StemSet(
            sources=sources,
            mixture=audio.samples,
            sample_rate=audio.sample_rate,
            identity=SEPARATOR_IDENTITY,
            residual_db=-180.0,
            confidence=0.8,
        )


def metric(
    key: str,
    value: float = 0.0,
    *,
    confidence: float = 0.9,
) -> Metric:
    return Metric(
        key=key,
        value=value,
        unit=None,
        evidence_type=EvidenceType.MEASURED,
        confidence=confidence,
        analyzer="fixture",
        analyzer_version="1.0.0",
    )


def scoring_metrics(**integrity: float) -> tuple[Metric, ...]:
    metrics = [
        metric("element.drums_relative_lufs"),
        metric("element.bass_relative_lufs"),
    ]
    metrics.extend(metric(f"stereo.feature_{index}") for index in range(6))
    metrics.extend(metric(f"tonal.erb_{index:02d}_relative_db") for index in range(24))
    metrics.extend(metric(f"dynamics.feature_{index}") for index in range(5))
    values = {
        "integrity.true_peak_dbtp": -1.0,
        "integrity.dc_offset_dbfs": -80.0,
        "integrity.clipped_sample_ratio": 0.0,
        "integrity.longest_clipped_run_ms": 0.0,
    }
    values.update(integrity)
    metrics.extend(metric(key, value) for key, value in values.items())
    return tuple(metrics)


def released_profile(
    metrics: tuple[Metric, ...],
    *,
    genre: PrimaryGenre = PrimaryGenre.RAP,
    half_width: float = 100.0,
) -> GenreProfile:
    features = {
        item.key: FeatureDistribution(
            median=item.value,
            q10=item.value - half_width,
            q90=item.value + half_width,
            mad=max(1.0, half_width / 2.0),
            sample_count=30,
        )
        for item in metrics
        if not item.key.startswith("integrity.")
        and item.key
        not in {"element.active_role_count", "element.separation_residual_db"}
    }
    return GenreProfile(
        genre=genre,
        version=f"{genre.value}-mixing-0.1.0",
        status="released",
        analysis_version=ANALYSIS_VERSION,
        formula_version=FORMULA_VERSION,
        source_count=50,
        split_counts={"calibration": 30, "validation": 10, "holdout": 10},
        separator=SEPARATOR_IDENTITY,
        features=features,
        analyzer_versions={item.analyzer: item.analyzer_version for item in metrics},
        corpus_summary={"artist_count": 25, "substyle_count": 4, "period_count": 4},
        validation_evidence={
            "ebu_passed": True,
            "validation_passed": True,
            "holdout_passed": True,
        },
    )
