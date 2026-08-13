from __future__ import annotations

import numpy as np
import pytest
from secondear_analysis.analyzers import (
    SignalIntegrityAnalyzer,
    StereoFieldAnalyzer,
    TonalBalanceAnalyzer,
)
from secondear_analysis.audio import AudioData
from secondear_analysis.loudness import EbuR128Analyzer


def _audio(samples: np.ndarray, sample_rate: int = 44_100) -> AudioData:
    return AudioData(
        samples=np.ascontiguousarray(samples, dtype=np.float32),
        sample_rate=sample_rate,
        source_format="WAV",
        subtype="FLOAT",
        duration_seconds=len(samples) / sample_rate,
        content_sha256="fixture",
    )


def _values(metrics: tuple) -> dict[str, float]:
    return {metric.key: metric.value for metric in metrics}


def test_ebu_loudness_and_peaks_for_stereo_sine() -> None:
    sample_rate = 48_000
    time = np.arange(sample_rate * 10, dtype=np.float64) / sample_rate
    signal = 0.1 * np.sin(2.0 * np.pi * 1_000.0 * time)
    report = EbuR128Analyzer().analyze(
        _audio(np.column_stack((signal, signal)), sample_rate)
    )
    values = _values(report.metrics)

    assert values["dynamics.integrated_lufs"] == pytest.approx(-20.0, abs=0.2)
    assert values["dynamics.loudness_range_lu"] == pytest.approx(0.0, abs=0.1)
    assert values["integrity.sample_peak_dbfs"] == pytest.approx(-20.0, abs=0.01)
    assert values["integrity.true_peak_dbtp"] == pytest.approx(-20.0, abs=0.1)
    assert np.isfinite(report.momentary_lufs).all()
    assert np.isfinite(report.short_term_lufs).all()


def test_true_peak_resolves_high_frequency_intersample_peak() -> None:
    sample_rate = 48_000
    sample_index = np.arange(sample_rate, dtype=np.float64)
    signal = 0.5 * np.sin(
        2.0 * np.pi * (sample_rate / 4.0) * sample_index / sample_rate + np.pi / 4.0
    )
    report = EbuR128Analyzer().analyze(
        _audio(np.column_stack((signal, signal)), sample_rate)
    )

    assert report.value("integrity.true_peak_dbtp") == pytest.approx(-6.0, abs=0.2)


def test_integrity_handles_silence_without_nan_or_infinity() -> None:
    metrics = SignalIntegrityAnalyzer().analyze(_audio(np.zeros((44_100, 2))))
    assert all(np.isfinite(metric.value) for metric in metrics)


def test_channel_swap_preserves_stereo_metrics() -> None:
    sample_rate = 44_100
    time = np.arange(sample_rate * 3, dtype=np.float64) / sample_rate
    samples = np.column_stack(
        (
            0.1 * np.sin(2.0 * np.pi * 440.0 * time),
            0.06 * np.sin(2.0 * np.pi * 880.0 * time + 0.3),
        )
    )
    analyzer = StereoFieldAnalyzer()
    original = _values(analyzer.analyze(_audio(samples)))
    swapped = _values(analyzer.analyze(_audio(samples[:, ::-1])))

    assert original.keys() == swapped.keys()
    for key in original:
        assert original[key] == pytest.approx(swapped[key], abs=1e-9)


def test_gain_preserves_tonal_and_stereo_shape_metrics() -> None:
    rng = np.random.default_rng(42)
    samples = rng.normal(0.0, 0.05, (44_100 * 3, 2))
    tonal = TonalBalanceAnalyzer()
    stereo = StereoFieldAnalyzer()

    base_tonal = _values(tonal.analyze(_audio(samples)))
    quiet_tonal = _values(tonal.analyze(_audio(samples * 0.25)))
    base_stereo = _values(stereo.analyze(_audio(samples)))
    quiet_stereo = _values(stereo.analyze(_audio(samples * 0.25)))

    for key in base_tonal:
        assert base_tonal[key] == pytest.approx(quiet_tonal[key], abs=1e-8)
    for key in base_stereo:
        assert base_stereo[key] == pytest.approx(quiet_stereo[key], abs=1e-8)


def test_gain_preserves_relative_loudness_and_dynamics_metrics() -> None:
    sample_rate = 44_100
    time = np.arange(sample_rate * 4, dtype=np.float64) / sample_rate
    signal = 0.1 * np.sin(2.0 * np.pi * 440.0 * time)
    samples = np.column_stack((signal, signal))
    analyzer = EbuR128Analyzer()

    base = _values(analyzer.analyze(_audio(samples)).metrics)
    quiet = _values(analyzer.analyze(_audio(samples * 0.25)).metrics)

    for key in (
        "dynamics.loudness_range_lu",
        "dynamics.short_term_p10_relative_lu",
        "dynamics.short_term_p50_relative_lu",
        "dynamics.short_term_p90_relative_lu",
        "dynamics.short_term_spread_lu",
        "dynamics.peak_to_loudness_db",
    ):
        assert base[key] == pytest.approx(quiet[key], abs=1e-6)


def test_stronger_dc_offset_increases_integrity_measurement() -> None:
    samples = np.zeros((44_100, 2), dtype=np.float64)
    analyzer = SignalIntegrityAnalyzer()

    low = _values(analyzer.analyze(_audio(samples + 0.0001)))
    high = _values(analyzer.analyze(_audio(samples + 0.01)))

    assert high["integrity.dc_offset_dbfs"] > low["integrity.dc_offset_dbfs"]


def test_stronger_limiting_reduces_crest_factor() -> None:
    sample_rate = 44_100
    time = np.arange(sample_rate * 3, dtype=np.float64) / sample_rate
    carrier = 0.25 * np.sin(2.0 * np.pi * 440.0 * time)
    carrier[::2_000] = 0.95
    stereo = np.column_stack((carrier, carrier))
    limited = np.tanh(stereo * 3.0) / np.tanh(3.0)
    analyzer = SignalIntegrityAnalyzer()

    original = _values(analyzer.analyze(_audio(stereo)))
    compressed = _values(analyzer.analyze(_audio(limited)))

    assert compressed["dynamics.crest_factor_db"] < original["dynamics.crest_factor_db"]


def test_stronger_low_frequency_boost_changes_target_erb_band_monotonically() -> None:
    sample_rate = 44_100
    time = np.arange(sample_rate * 3, dtype=np.float64) / sample_rate
    high = 0.03 * np.sin(2.0 * np.pi * 4_000.0 * time)
    low = np.sin(2.0 * np.pi * 100.0 * time)
    analyzer = TonalBalanceAnalyzer()

    def low_band_value(low_gain: float) -> float:
        samples = np.column_stack((high + low_gain * low, high + low_gain * low))
        metrics = analyzer.analyze(_audio(samples))
        metric = next(
            item
            for item in metrics
            if item.parameters["low_hz"] <= 100.0 < item.parameters["high_hz"]
        )
        return metric.value

    assert low_band_value(0.2) > low_band_value(0.1) > low_band_value(0.05)


def test_stronger_lr_imbalance_increases_balance_metric() -> None:
    sample_rate = 44_100
    time = np.arange(sample_rate * 3, dtype=np.float64) / sample_rate
    signal = 0.1 * np.sin(2.0 * np.pi * 440.0 * time)
    analyzer = StereoFieldAnalyzer()

    balanced = _values(analyzer.analyze(_audio(np.column_stack((signal, signal)))))
    imbalanced = _values(
        analyzer.analyze(_audio(np.column_stack((signal, signal * 0.25))))
    )

    assert imbalanced["stereo.lr_balance_db"] > balanced["stereo.lr_balance_db"]


def test_inverted_channels_expose_phase_and_mono_cancellation() -> None:
    sample_rate = 44_100
    time = np.arange(sample_rate * 3, dtype=np.float64) / sample_rate
    signal = 0.1 * np.sin(2.0 * np.pi * 440.0 * time)
    values = _values(
        StereoFieldAnalyzer().analyze(_audio(np.column_stack((signal, -signal))))
    )

    assert values["stereo.correlation_p05"] == pytest.approx(-1.0, abs=1e-9)
    assert values["stereo.negative_correlation_ratio"] == pytest.approx(1.0)
    assert values["stereo.mono_fold_down_delta_db"] < -100.0


def test_stronger_clipping_increases_integrity_measurements() -> None:
    sample_rate = 44_100
    time = np.arange(sample_rate, dtype=np.float64) / sample_rate
    source = np.column_stack(
        (
            1.4 * np.sin(2.0 * np.pi * 1_000.0 * time),
            1.4 * np.sin(2.0 * np.pi * 1_000.0 * time),
        )
    )
    lightly_clipped = np.clip(source, -0.999, 0.999)
    heavily_clipped = np.where(np.abs(source) > 0.5, np.sign(source), source)
    analyzer = SignalIntegrityAnalyzer()
    light = _values(analyzer.analyze(_audio(lightly_clipped)))
    heavy = _values(analyzer.analyze(_audio(heavily_clipped)))

    assert (
        heavy["integrity.clipped_sample_ratio"]
        > light["integrity.clipped_sample_ratio"]
    )
    assert (
        heavy["integrity.longest_clipped_run_ms"]
        > light["integrity.longest_clipped_run_ms"]
    )


def test_clipping_metric_records_bounded_time_intervals() -> None:
    sample_rate = 44_100
    samples = np.zeros((sample_rate, 2), dtype=np.float64)
    samples[4_410:4_851] = 1.0

    metrics = SignalIntegrityAnalyzer().analyze(_audio(samples, sample_rate))
    clipped = next(
        metric for metric in metrics if metric.key == "integrity.clipped_sample_ratio"
    )

    assert clipped.parameters["clipped_intervals"] == [
        {"start_seconds": pytest.approx(0.1), "end_seconds": pytest.approx(0.11)}
    ]
