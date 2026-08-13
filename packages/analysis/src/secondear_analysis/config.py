"""Versioned constants for Mixing v1.

Thresholds live here so analyzer code does not acquire undocumented magic
numbers. Changing scoring behavior requires a formula version change.
"""

from __future__ import annotations

from dataclasses import dataclass

ANALYSIS_VERSION = "mixing-analysis-0.1.0"
FORMULA_VERSION = "mixing-score-0.1.0"
DECODER_VERSION = "soundfile-decoder-0.1.0"
LOUDNESS_VERSION = "libebur128-meter-0.1.0"
SIGNAL_VERSION = "signal-integrity-0.1.0"
STEREO_VERSION = "stereo-field-0.1.0"
TONAL_VERSION = "erb-tonal-balance-0.1.0"
ELEMENT_VERSION = "four-role-balance-0.1.0"
REFERENCE_VERSION = "metric-delta-0.1.0"

MIN_DURATION_SECONDS = 30.0
MAX_DURATION_SECONDS = 600.0
MIN_SAMPLE_RATE = 44_100
REQUIRED_CHANNELS = 2
SUPPORTED_FORMATS = frozenset({"WAV", "FLAC"})
SUPPORTED_SUFFIXES = frozenset({".wav", ".flac"})

CONFIDENCE_THRESHOLD = 0.65
SEPARATION_CONFIDENCE_CAP = 0.80
MAX_SEPARATION_RESIDUAL_DB = -20.0
CLIPPING_AMPLITUDE = 0.9999

ACTIVE_FRAME_ABSOLUTE_DBFS = -70.0
ACTIVE_FRAME_RELATIVE_DB = 60.0

BLOCK_MAX_PENALTIES: dict[str, float] = {
    "element_balance": 4.0,
    "stereo": 3.0,
    "tonal": 2.5,
    "dynamics": 2.0,
    "integrity": 2.0,
}

PRIMARY_GENRES = ("rap", "pop", "r_and_b", "rock", "country", "electronic")
STEM_NAMES = ("vocals", "drums", "bass", "other")


@dataclass(frozen=True, slots=True)
class ProfileRequirements:
    """Minimum lawful-corpus evidence needed for a released profile."""

    calibration: int = 30
    validation: int = 10
    holdout: int = 10
    total: int = 50
    max_tracks_per_artist: int = 2


PROFILE_REQUIREMENTS = ProfileRequirements()
