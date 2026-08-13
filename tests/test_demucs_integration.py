from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest
from secondear_analysis.audio import SoundFileDecoder
from secondear_analysis.config import MAX_SEPARATION_RESIDUAL_DB, STEM_NAMES
from secondear_analysis.separation import DemucsSeparator


@pytest.mark.integration
def test_real_htdemucs_ft_four_role_separation(stereo_wav: Path) -> None:
    if os.environ.get("SECONDEAR_RUN_DEMUCS") != "1":
        pytest.skip(
            "Set SECONDEAR_RUN_DEMUCS=1 to run the model-backed integration test."
        )

    audio = SoundFileDecoder().decode(stereo_wav)
    stems = DemucsSeparator().separate(audio)

    assert tuple(stems.sources) == STEM_NAMES
    assert all(source.shape == stems.mixture.shape for source in stems.sources.values())
    assert all(np.isfinite(source).all() for source in stems.sources.values())
    assert stems.identity.model == "htdemucs_ft"
    assert len(stems.identity.model_checksum) == 64
    assert stems.residual_db <= MAX_SEPARATION_RESIDUAL_DB
    assert stems.confidence == pytest.approx(0.8)
