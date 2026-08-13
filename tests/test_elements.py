from __future__ import annotations

import numpy as np
from secondear_analysis.config import STEM_NAMES
from secondear_analysis.elements import ElementBalanceAnalyzer
from secondear_analysis.separation import StemSet

from .helpers import SEPARATOR_IDENTITY


def _stem_set(vocal_gain: float) -> StemSet:
    sample_rate = 44_100
    time = np.arange(sample_rate * 4, dtype=np.float64) / sample_rate
    frequencies = {
        "vocals": 1_000.0,
        "drums": 4_000.0,
        "bass": 100.0,
        "other": 400.0,
    }
    sources = {
        name: np.ascontiguousarray(
            np.column_stack(
                (
                    0.02
                    * (vocal_gain if name == "vocals" else 1.0)
                    * np.sin(2.0 * np.pi * frequencies[name] * time),
                    0.02
                    * (vocal_gain if name == "vocals" else 1.0)
                    * np.sin(2.0 * np.pi * frequencies[name] * time),
                )
            ),
            dtype=np.float32,
        )
        for name in STEM_NAMES
    }
    mixture = np.ascontiguousarray(sum(sources.values()), dtype=np.float32)
    return StemSet(
        sources=sources,
        mixture=mixture,
        sample_rate=sample_rate,
        identity=SEPARATOR_IDENTITY,
        residual_db=-180.0,
        confidence=0.8,
    )


def test_stronger_vocal_level_change_moves_relative_balance_monotonically() -> None:
    analyzer = ElementBalanceAnalyzer()

    values = []
    for gain in (1.0, 2.0, 4.0):
        metrics = analyzer.analyze(_stem_set(gain))
        values.append(
            next(
                item.value
                for item in metrics
                if item.key == "element.vocals_relative_lufs"
            )
        )

    assert values[2] > values[1] > values[0]
