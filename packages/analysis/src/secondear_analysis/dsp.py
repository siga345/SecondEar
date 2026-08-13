"""Shared deterministic DSP helpers."""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np
from numpy.typing import NDArray

from .config import ACTIVE_FRAME_ABSOLUTE_DBFS, ACTIVE_FRAME_RELATIVE_DB

EPSILON = np.finfo(np.float64).tiny


def amplitude_to_db(value: float, *, floor: float = -180.0) -> float:
    """Convert a non-negative linear amplitude to dB."""

    if not np.isfinite(value) or value <= 0.0:
        return floor
    return max(floor, float(20.0 * np.log10(value)))


def power_to_db(value: float, *, floor: float = -180.0) -> float:
    """Convert non-negative linear power to dB."""

    if not np.isfinite(value) or value <= 0.0:
        return floor
    return max(floor, float(10.0 * np.log10(value)))


def finite_percentile(values: NDArray[np.floating], percentile: float) -> float:
    finite = np.asarray(values, dtype=np.float64)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return -180.0
    return float(np.percentile(finite, percentile))


def frame_audio(
    samples: NDArray[np.floating], frame_size: int, hop_size: int
) -> Iterator[tuple[int, NDArray[np.floating]]]:
    """Yield complete overlapping frames without inventing padded evidence."""

    if frame_size <= 0 or hop_size <= 0:
        raise ValueError("Frame and hop sizes must be positive.")
    for start in range(0, max(0, len(samples) - frame_size + 1), hop_size):
        yield start, samples[start : start + frame_size]


def active_frames(
    samples: NDArray[np.floating], sample_rate: int, *, frame_seconds: float = 0.1
) -> tuple[list[int], list[NDArray[np.floating]]]:
    """Select frames above both an absolute and track-relative energy gate."""

    frame_size = max(1, round(sample_rate * frame_seconds))
    energies: list[float] = []
    starts: list[int] = []
    frames: list[NDArray[np.floating]] = []
    for start, frame in frame_audio(samples, frame_size, frame_size):
        rms = float(np.sqrt(np.mean(np.square(frame, dtype=np.float64))))
        energies.append(amplitude_to_db(rms))
        starts.append(start)
        frames.append(frame)
    if not energies:
        return [], []
    peak = max(energies)
    threshold = max(ACTIVE_FRAME_ABSOLUTE_DBFS, peak - ACTIVE_FRAME_RELATIVE_DB)
    selected = [index for index, value in enumerate(energies) if value >= threshold]
    return [starts[index] for index in selected], [frames[index] for index in selected]


def erb_band_edges(sample_rate: int, bands: int = 24) -> NDArray[np.float64]:
    """Return equal-ERB-rate band edges from 20 Hz through 20 kHz/Nyquist."""

    high = min(20_000.0, sample_rate / 2.0)
    low_rate = 21.4 * np.log10(1.0 + 0.00437 * 20.0)
    high_rate = 21.4 * np.log10(1.0 + 0.00437 * high)
    rates = np.linspace(low_rate, high_rate, bands + 1)
    return (np.power(10.0, rates / 21.4) - 1.0) / 0.00437


def median_erb_power(
    samples: NDArray[np.floating],
    sample_rate: int,
    *,
    bands: int = 24,
    frame_size: int = 4096,
    hop_size: int = 2048,
) -> NDArray[np.float64]:
    """Return the median active-frame power in equal-ERB-rate bands."""

    mono = np.mean(samples, axis=1) if samples.ndim == 2 else samples
    window = np.hanning(frame_size).astype(np.float64)
    frequencies = np.fft.rfftfreq(frame_size, 1.0 / sample_rate)
    edges = erb_band_edges(sample_rate, bands)
    rows: list[NDArray[np.float64]] = []
    frame_rms: list[float] = []
    for _, frame in frame_audio(mono, frame_size, hop_size):
        values = np.asarray(frame, dtype=np.float64)
        frame_rms.append(amplitude_to_db(float(np.sqrt(np.mean(values * values)))))
        spectrum = np.fft.rfft(values * window)
        power = np.abs(spectrum) ** 2
        row = np.zeros(bands, dtype=np.float64)
        for band in range(bands):
            include_high = band == bands - 1
            mask = (frequencies >= edges[band]) & (
                (frequencies <= edges[band + 1])
                if include_high
                else (frequencies < edges[band + 1])
            )
            row[band] = float(np.sum(power[mask]))
        rows.append(row)
    if not rows:
        return np.full(bands, EPSILON, dtype=np.float64)
    peak = max(frame_rms)
    gate = max(ACTIVE_FRAME_ABSOLUTE_DBFS, peak - ACTIVE_FRAME_RELATIVE_DB)
    selected = [
        row for row, level in zip(rows, frame_rms, strict=True) if level >= gate
    ]
    if not selected:
        selected = rows
    return np.median(np.vstack(selected), axis=0)


def longest_true_run(mask: NDArray[np.bool_]) -> int:
    """Return the longest contiguous run in a boolean vector."""

    if mask.size == 0 or not bool(np.any(mask)):
        return 0
    padded = np.concatenate(([False], mask, [False])).astype(np.int8)
    transitions = np.diff(padded)
    starts = np.flatnonzero(transitions == 1)
    ends = np.flatnonzero(transitions == -1)
    return int(np.max(ends - starts))


def true_run_ranges(
    mask: NDArray[np.bool_], sample_rate: int, *, limit: int = 64
) -> tuple[tuple[float, float], ...]:
    """Return bounded half-open time ranges for contiguous true samples."""

    if mask.size == 0 or not bool(np.any(mask)):
        return ()
    padded = np.concatenate(([False], mask, [False])).astype(np.int8)
    transitions = np.diff(padded)
    starts = np.flatnonzero(transitions == 1)
    ends = np.flatnonzero(transitions == -1)
    return tuple(
        (float(start / sample_rate), float(end / sample_rate))
        for start, end in zip(starts[:limit], ends[:limit], strict=True)
    )
