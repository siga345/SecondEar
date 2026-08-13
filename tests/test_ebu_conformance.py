from __future__ import annotations

import os
from pathlib import Path

import pytest
import soundfile as sf
from secondear_analysis.loudness import EbuR128Analyzer


@pytest.mark.ebu
@pytest.mark.parametrize(
    ("filename", "expected_lufs"),
    [
        ("seq-3341-1-16bit.wav", -23.0),
        ("seq-3341-2-16bit.wav", -33.0),
        ("seq-3341-3-16bit-v02.wav", -23.0),
        ("seq-3341-4-16bit-v02.wav", -23.0),
        ("seq-3341-5-16bit-v02.wav", -23.0),
    ],
)
def test_official_ebu_tech_3341_integrated_loudness(
    filename: str, expected_lufs: float
) -> None:
    root_value = os.environ.get("SECONDEAR_EBU_TEST_SET")
    if not root_value:
        pytest.skip(
            "Set SECONDEAR_EBU_TEST_SET to the official EBU Loudness Test Set directory."
        )
    path = Path(root_value) / filename
    if not path.is_file():
        pytest.skip(f"Official EBU fixture is absent: {filename}")
    samples, sample_rate = sf.read(path, dtype="float32", always_2d=True)

    report = EbuR128Analyzer().analyze_samples(samples, sample_rate)
    measured = report.value("dynamics.integrated_lufs")
    assert measured == pytest.approx(expected_lufs, abs=0.1)


@pytest.mark.ebu
@pytest.mark.parametrize(
    ("filename", "expected_lra"),
    [
        ("seq-3342-1-16bit.wav", 10.0),
        ("seq-3342-2-16bit.wav", 5.0),
        ("seq-3342-3-16bit.wav", 20.0),
        ("seq-3342-4-16bit.wav", 15.0),
    ],
)
def test_official_ebu_tech_3342_loudness_range(
    filename: str, expected_lra: float
) -> None:
    root_value = os.environ.get("SECONDEAR_EBU_TEST_SET")
    if not root_value:
        pytest.skip(
            "Set SECONDEAR_EBU_TEST_SET to the official EBU Loudness Test Set directory."
        )
    path = Path(root_value) / filename
    if not path.is_file():
        pytest.skip(f"Official EBU fixture is absent: {filename}")
    samples, sample_rate = sf.read(path, dtype="float32", always_2d=True)

    report = EbuR128Analyzer().analyze_samples(samples, sample_rate)
    measured = report.value("dynamics.loudness_range_lu")
    assert measured == pytest.approx(expected_lra, abs=1.0)


@pytest.mark.ebu
@pytest.mark.parametrize(
    ("filename", "expected_dbtp"),
    [
        ("seq-3341-15-24bit.wav", -6.0),
        ("seq-3341-16-24bit.wav", -6.0),
        ("seq-3341-17-24bit.wav", -6.0),
        ("seq-3341-18-24bit.wav", -6.0),
        ("seq-3341-19-24bit.wav", 3.0),
        ("seq-3341-20-24bit.wav", 0.0),
        ("seq-3341-21-24bit.wav", 0.0),
        ("seq-3341-22-24bit.wav", 0.0),
        ("seq-3341-23-24bit.wav", 0.0),
    ],
)
def test_official_ebu_tech_3341_true_peak(filename: str, expected_dbtp: float) -> None:
    root_value = os.environ.get("SECONDEAR_EBU_TEST_SET")
    if not root_value:
        pytest.skip(
            "Set SECONDEAR_EBU_TEST_SET to the official EBU Loudness Test Set directory."
        )
    path = Path(root_value) / filename
    if not path.is_file():
        pytest.skip(f"Official EBU fixture is absent: {filename}")
    samples, sample_rate = sf.read(path, dtype="float32", always_2d=True)

    report = EbuR128Analyzer().analyze_samples(samples, sample_rate)
    measured = report.value("integrity.true_peak_dbtp")
    assert expected_dbtp - 0.4 <= measured <= expected_dbtp + 0.2
