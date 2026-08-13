"""EBU R128 loudness and peak measurements backed by libebur128."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pyebur128
from numpy.typing import NDArray

from .audio import AudioData
from .config import LOUDNESS_VERSION
from .dsp import amplitude_to_db, finite_percentile
from .models import EvidenceType, Metric


@dataclass(frozen=True, slots=True)
class LoudnessReport:
    metrics: tuple[Metric, ...]
    momentary_lufs: NDArray[np.float64]
    short_term_lufs: NDArray[np.float64]
    timeline_seconds: NDArray[np.float64]

    def value(self, key: str) -> float:
        for metric in self.metrics:
            if metric.key == key:
                return metric.value
        raise KeyError(key)


class EbuR128Analyzer:
    """Measure EBU M/S/I loudness, LRA, sample peak, and true peak."""

    name = "loudness"
    version = LOUDNESS_VERSION
    confidence = 0.99

    def analyze(self, audio: AudioData) -> LoudnessReport:
        return self.analyze_samples(audio.samples, audio.sample_rate)

    def analyze_samples(
        self, samples: NDArray[np.floating], sample_rate: int
    ) -> LoudnessReport:
        channels = int(samples.shape[1])
        mode = int(
            pyebur128.MeasurementMode.MODE_TRUE_PEAK
            | pyebur128.MeasurementMode.MODE_LRA
            | pyebur128.MeasurementMode.MODE_I
        )
        state = pyebur128.R128State(channels, sample_rate, mode)
        step_frames = max(1, sample_rate // 10)
        momentary: list[float] = []
        short_term: list[float] = []
        times: list[float] = []

        for start in range(0, len(samples), step_frames):
            chunk = np.ascontiguousarray(
                samples[start : start + step_frames], dtype=np.float32
            )
            if chunk.size == 0:
                continue
            state.add_frames(chunk.reshape(-1), len(chunk))
            elapsed = (start + len(chunk)) / sample_rate
            times.append(elapsed)
            momentary.append(
                _finite_or_floor(pyebur128.get_loudness_momentary(state))
                if elapsed >= 0.4
                else -180.0
            )
            short_term.append(
                _finite_or_floor(pyebur128.get_loudness_shortterm(state))
                if elapsed >= 3.0
                else -180.0
            )

        integrated = _finite_or_floor(pyebur128.get_loudness_global(state))
        lra = max(0.0, _finite_or_zero(pyebur128.get_loudness_range(state)))
        sample_peak = max(
            pyebur128.get_sample_peak(state, channel) for channel in range(channels)
        )
        true_peak = max(
            pyebur128.get_true_peak(state, channel) for channel in range(channels)
        )
        momentary_array = np.asarray(momentary, dtype=np.float64)
        short_array = np.asarray(short_term, dtype=np.float64)
        finite_short = short_array[short_array > -179.0]
        short_p10 = finite_percentile(finite_short, 10)
        short_p50 = finite_percentile(finite_short, 50)
        short_p90 = finite_percentile(finite_short, 90)
        true_peak_dbtp = amplitude_to_db(true_peak)

        metrics = (
            _metric("dynamics.integrated_lufs", integrated, "LUFS"),
            _metric("dynamics.loudness_range_lu", lra, "LU"),
            _metric("dynamics.short_term_p10_lufs", short_p10, "LUFS"),
            _metric("dynamics.short_term_p50_lufs", short_p50, "LUFS"),
            _metric("dynamics.short_term_p90_lufs", short_p90, "LUFS"),
            _metric(
                "dynamics.short_term_p10_relative_lu",
                short_p10 - integrated,
                "LU",
            ),
            _metric(
                "dynamics.short_term_p50_relative_lu",
                short_p50 - integrated,
                "LU",
            ),
            _metric(
                "dynamics.short_term_p90_relative_lu",
                short_p90 - integrated,
                "LU",
            ),
            _metric(
                "dynamics.short_term_spread_lu",
                float(np.std(finite_short)) if finite_short.size else 0.0,
                "LU",
            ),
            _metric(
                "dynamics.peak_to_loudness_db",
                true_peak_dbtp - integrated,
                "dB",
            ),
            _metric("integrity.sample_peak_dbfs", amplitude_to_db(sample_peak), "dBFS"),
            _metric("integrity.true_peak_dbtp", true_peak_dbtp, "dBTP"),
        )
        return LoudnessReport(
            metrics=metrics,
            momentary_lufs=momentary_array,
            short_term_lufs=short_array,
            timeline_seconds=np.asarray(times, dtype=np.float64),
        )


def _metric(key: str, value: float, unit: str) -> Metric:
    return Metric(
        key=key,
        value=float(value),
        unit=unit,
        evidence_type=EvidenceType.MEASURED,
        confidence=0.99,
        analyzer="loudness",
        analyzer_version=LOUDNESS_VERSION,
        parameters={
            "standard": "EBU R128 / ITU-R BS.1770",
            "step_ms": 100,
            "libebur128_version": pyebur128.get_libebur128_version(),
        },
    )


def _finite_or_floor(value: float) -> float:
    return float(value) if np.isfinite(value) else -180.0


def _finite_or_zero(value: float) -> float:
    return float(value) if np.isfinite(value) else 0.0
