"""Signal integrity, stereo-field, tonal, and dynamics analyzers."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.signal import welch

from .audio import AudioData
from .config import (
    CLIPPING_AMPLITUDE,
    SIGNAL_VERSION,
    STEREO_VERSION,
    TONAL_VERSION,
)
from .dsp import (
    amplitude_to_db,
    erb_band_edges,
    frame_audio,
    longest_true_run,
    median_erb_power,
    power_to_db,
    true_run_ranges,
)
from .models import EvidenceType, Metric


class SignalIntegrityAnalyzer:
    name = "signal_integrity"
    version = SIGNAL_VERSION

    def analyze(self, audio: AudioData) -> tuple[Metric, ...]:
        samples = np.asarray(audio.samples, dtype=np.float64)
        rms = float(np.sqrt(np.mean(samples * samples)))
        peak = float(np.max(np.abs(samples)))
        dc = float(np.max(np.abs(np.mean(samples, axis=0))))
        clipped_samples = np.abs(samples) >= CLIPPING_AMPLITUDE
        clipped_by_frame = np.any(clipped_samples, axis=1)
        clipped_ratio = float(np.mean(clipped_samples))
        longest_run = longest_true_run(clipped_by_frame)
        longest_run_ms = 1000.0 * longest_run / audio.sample_rate
        clipped_intervals = [
            {"start_seconds": start, "end_seconds": end}
            for start, end in true_run_ranges(clipped_by_frame, audio.sample_rate)
        ]
        crest = amplitude_to_db(peak) - amplitude_to_db(rms)
        return (
            _metric(
                "dynamics.crest_factor_db",
                crest,
                "dB",
                SIGNAL_VERSION,
                EvidenceType.DERIVED,
            ),
            _metric("integrity.rms_dbfs", amplitude_to_db(rms), "dBFS", SIGNAL_VERSION),
            _metric(
                "integrity.dc_offset_dbfs", amplitude_to_db(dc), "dBFS", SIGNAL_VERSION
            ),
            _metric(
                "integrity.clipped_sample_ratio",
                clipped_ratio,
                "ratio",
                SIGNAL_VERSION,
                parameters={"clipped_intervals": clipped_intervals},
            ),
            _metric(
                "integrity.longest_clipped_run_ms",
                longest_run_ms,
                "ms",
                SIGNAL_VERSION,
                parameters={"clipped_intervals": clipped_intervals},
            ),
        )


class StereoFieldAnalyzer:
    name = "stereo_field"
    version = STEREO_VERSION

    def analyze(self, audio: AudioData) -> tuple[Metric, ...]:
        samples = np.asarray(audio.samples, dtype=np.float64)
        left = samples[:, 0]
        right = samples[:, 1]
        left_rms = float(np.sqrt(np.mean(left * left)))
        right_rms = float(np.sqrt(np.mean(right * right)))
        lr_delta = abs(amplitude_to_db(left_rms) - amplitude_to_db(right_rms))
        correlations = _correlation_timeline(samples, audio.sample_rate)
        mid = (left + right) * 0.5
        side = (left - right) * 0.5
        stereo_power = float(np.mean((left * left + right * right) * 0.5))
        mono_power = float(np.mean(mid * mid))
        frequencies, mid_psd = welch(mid, fs=audio.sample_rate, nperseg=4096)
        _, side_psd = welch(side, fs=audio.sample_rate, nperseg=4096)

        metrics: list[Metric] = [
            _metric("stereo.lr_balance_db", lr_delta, "dB", STEREO_VERSION),
            _metric(
                "stereo.correlation_p05",
                float(np.percentile(correlations, 5)) if correlations.size else 0.0,
                "coefficient",
                STEREO_VERSION,
            ),
            _metric(
                "stereo.correlation_median",
                float(np.median(correlations)) if correlations.size else 0.0,
                "coefficient",
                STEREO_VERSION,
            ),
            _metric(
                "stereo.negative_correlation_ratio",
                float(np.mean(correlations < 0.0)) if correlations.size else 0.0,
                "ratio",
                STEREO_VERSION,
            ),
            _metric(
                "stereo.mono_fold_down_delta_db",
                power_to_db(mono_power) - power_to_db(stereo_power),
                "dB",
                STEREO_VERSION,
            ),
        ]
        for name, low, high in (
            ("low", 20.0, 120.0),
            ("low_mid", 120.0, 500.0),
            ("mid", 500.0, 4_000.0),
            ("high", 4_000.0, 20_000.0),
        ):
            mask = (frequencies >= low) & (
                frequencies < min(high, audio.sample_rate / 2.0)
            )
            mid_power = float(np.mean(mid_psd[mask])) if np.any(mask) else 0.0
            side_power = float(np.mean(side_psd[mask])) if np.any(mask) else 0.0
            width_db = (
                -180.0
                if mid_power <= np.finfo(np.float64).tiny
                and side_power <= np.finfo(np.float64).tiny
                else power_to_db(side_power) - power_to_db(mid_power)
            )
            metrics.append(
                _metric(
                    f"stereo.side_to_mid_{name}_db",
                    width_db,
                    "dB",
                    STEREO_VERSION,
                )
            )
        return tuple(metrics)


class TonalBalanceAnalyzer:
    name = "tonal_balance"
    version = TONAL_VERSION

    def analyze(self, audio: AudioData) -> tuple[Metric, ...]:
        power = median_erb_power(audio.samples, audio.sample_rate, bands=24)
        total = max(float(np.sum(power)), np.finfo(np.float64).tiny)
        normalized = power / total
        edges = erb_band_edges(audio.sample_rate, 24)
        return tuple(
            Metric(
                key=f"tonal.erb_{index:02d}_relative_db",
                value=power_to_db(float(value)),
                unit="dB relative",
                evidence_type=EvidenceType.MEASURED,
                confidence=0.96,
                analyzer=self.name,
                analyzer_version=self.version,
                parameters={
                    "low_hz": round(float(edges[index]), 3),
                    "high_hz": round(float(edges[index + 1]), 3),
                    "bands": 24,
                    "aggregation": "median active-frame power",
                },
            )
            for index, value in enumerate(normalized)
        )


def _correlation_timeline(
    samples: NDArray[np.float64], sample_rate: int
) -> NDArray[np.float64]:
    frame_size = max(1024, round(sample_rate * 0.4))
    hop_size = max(512, frame_size // 2)
    values: list[float] = []
    levels: list[float] = []
    for _, frame in frame_audio(samples, frame_size, hop_size):
        left = frame[:, 0]
        right = frame[:, 1]
        denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
        values.append(float(np.dot(left, right) / denominator) if denominator else 0.0)
        levels.append(amplitude_to_db(float(np.sqrt(np.mean(frame * frame)))))
    if not values:
        return np.empty(0, dtype=np.float64)
    gate = max(-70.0, max(levels) - 60.0)
    return np.asarray(
        [value for value, level in zip(values, levels, strict=True) if level >= gate],
        dtype=np.float64,
    )


def _metric(
    key: str,
    value: float,
    unit: str,
    version: str,
    evidence_type: EvidenceType = EvidenceType.MEASURED,
    parameters: dict[str, object] | None = None,
) -> Metric:
    return Metric(
        key=key,
        value=float(value),
        unit=unit,
        evidence_type=evidence_type,
        confidence=0.98,
        analyzer=key.split(".", 1)[0],
        analyzer_version=version,
        parameters=parameters or {},
    )
