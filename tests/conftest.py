from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf


@pytest.fixture(scope="session")
def stereo_wav(tmp_path_factory: pytest.TempPathFactory) -> Path:
    directory = tmp_path_factory.mktemp("audio")
    path = directory / "stereo.wav"
    sample_rate = 44_100
    time = np.arange(sample_rate * 30, dtype=np.float64) / sample_rate
    left = 0.10 * np.sin(2.0 * np.pi * 440.0 * time)
    right = 0.08 * np.sin(2.0 * np.pi * 660.0 * time + 0.2)
    sf.write(path, np.column_stack((left, right)), sample_rate, subtype="PCM_24")
    return path


@pytest.fixture(scope="session")
def stereo_flac(tmp_path_factory: pytest.TempPathFactory) -> Path:
    directory = tmp_path_factory.mktemp("audio-flac")
    path = directory / "stereo.flac"
    sample_rate = 44_100
    time = np.arange(sample_rate * 30, dtype=np.float64) / sample_rate
    signal = 0.08 * np.sin(2.0 * np.pi * 330.0 * time)
    sf.write(path, np.column_stack((signal, signal)), sample_rate, subtype="PCM_24")
    return path
