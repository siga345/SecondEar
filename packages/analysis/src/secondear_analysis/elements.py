"""Genre-benchmarkable element-balance evidence from estimated source roles."""

from __future__ import annotations

import numpy as np

from .config import ELEMENT_VERSION, STEM_NAMES
from .dsp import median_erb_power
from .loudness import EbuR128Analyzer, LoudnessReport
from .models import EvidenceType, Metric
from .separation import StemSet


class ElementBalanceAnalyzer:
    """Measure relative loudness and an ERB overlap proxy for four source roles."""

    name = "element_balance"
    version = ELEMENT_VERSION
    presence_below_mix_lu = 35.0

    def __init__(self, loudness: EbuR128Analyzer | None = None) -> None:
        self.loudness = loudness or EbuR128Analyzer()

    def analyze(self, stems: StemSet) -> tuple[Metric, ...]:
        mixture_report = self.loudness.analyze_samples(stems.mixture, stems.sample_rate)
        mixture_lufs = mixture_report.value("dynamics.integrated_lufs")
        reports: dict[str, LoudnessReport] = {}
        active: list[str] = []
        metrics: list[Metric] = [
            self._metric(
                "element.separation_residual_db",
                stems.residual_db,
                "dB relative",
                EvidenceType.ESTIMATED,
                stems.confidence,
            )
        ]

        for name in STEM_NAMES:
            report = self.loudness.analyze_samples(
                stems.sources[name], stems.sample_rate
            )
            reports[name] = report
            relative_lufs = report.value("dynamics.integrated_lufs") - mixture_lufs
            if (
                np.isfinite(relative_lufs)
                and relative_lufs >= -self.presence_below_mix_lu
            ):
                active.append(name)
                metrics.append(
                    self._metric(
                        f"element.{name}_relative_lufs",
                        relative_lufs,
                        "LU",
                        EvidenceType.ESTIMATED,
                        stems.confidence,
                    )
                )
                timeline_delta = _aligned_short_term_delta(report, mixture_report)
                if timeline_delta.size:
                    metrics.extend(
                        (
                            self._metric(
                                f"element.{name}_short_term_median_lu",
                                float(np.median(timeline_delta)),
                                "LU",
                                EvidenceType.ESTIMATED,
                                stems.confidence,
                            ),
                            self._metric(
                                f"element.{name}_short_term_spread_lu",
                                float(np.std(timeline_delta)),
                                "LU",
                                EvidenceType.ESTIMATED,
                                stems.confidence,
                            ),
                        )
                    )

        band_power = {
            name: median_erb_power(stems.sources[name], stems.sample_rate, bands=24)
            for name in active
        }
        for name in active:
            if len(active) == 1:
                continue
            masker = sum(
                (band_power[other] for other in active if other != name),
                start=np.zeros(24, dtype=np.float64),
            )
            margins = 10.0 * np.log10(
                np.maximum(band_power[name], 1e-18) / np.maximum(masker, 1e-18)
            )
            metrics.append(
                self._metric(
                    f"element.{name}_mask_margin_median_db",
                    float(np.median(margins)),
                    "dB",
                    EvidenceType.ESTIMATED,
                    min(stems.confidence, 0.72),
                )
            )

        metrics.append(
            self._metric(
                "element.active_role_count",
                float(len(active)),
                "count",
                EvidenceType.DERIVED,
                stems.confidence,
            )
        )
        return tuple(metrics)

    def _metric(
        self,
        key: str,
        value: float,
        unit: str,
        evidence_type: EvidenceType,
        confidence: float,
    ) -> Metric:
        return Metric(
            key=key,
            value=float(value),
            unit=unit,
            evidence_type=evidence_type,
            confidence=float(confidence),
            analyzer=self.name,
            analyzer_version=self.version,
            parameters={
                "roles": list(STEM_NAMES),
                "presence_below_mix_lu": self.presence_below_mix_lu,
            },
        )


def _aligned_short_term_delta(
    source: LoudnessReport, mixture: LoudnessReport
) -> np.ndarray:
    length = min(len(source.short_term_lufs), len(mixture.short_term_lufs))
    if length == 0:
        return np.empty(0, dtype=np.float64)
    source_values = source.short_term_lufs[:length]
    mixture_values = mixture.short_term_lufs[:length]
    valid = (source_values > -179.0) & (mixture_values > -179.0)
    return source_values[valid] - mixture_values[valid]
