"""Lossless audio decoding and Mixing v1 input validation."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf
from numpy.typing import NDArray

from .config import (
    DECODER_VERSION,
    MAX_DURATION_SECONDS,
    MIN_DURATION_SECONDS,
    MIN_SAMPLE_RATE,
    REQUIRED_CHANNELS,
    SUPPORTED_FORMATS,
    SUPPORTED_SUFFIXES,
)
from .errors import DecoderError, InputValidationError


@dataclass(frozen=True, slots=True)
class AudioData:
    """Decoded interleaved-domain samples shaped as frames by channels."""

    samples: NDArray[np.float32]
    sample_rate: int
    source_format: str
    subtype: str
    duration_seconds: float
    content_sha256: str
    decoder_version: str = DECODER_VERSION

    @property
    def channels(self) -> int:
        return int(self.samples.shape[1])


class SoundFileDecoder:
    """Decode and validate stereo lossless WAV/FLAC input with libsndfile."""

    version = DECODER_VERSION

    def decode(self, path: str | Path) -> AudioData:
        source = Path(path)
        if source.suffix.lower() not in SUPPORTED_SUFFIXES:
            raise InputValidationError("Mixing v1 accepts only WAV and FLAC files.")
        if not source.is_file():
            raise InputValidationError(
                "The audio source does not exist or is not a regular file."
            )

        try:
            info = sf.info(source)
        except (RuntimeError, TypeError) as exc:
            raise DecoderError("The audio source could not be decoded.") from exc

        source_format = info.format.upper()
        if source_format not in SUPPORTED_FORMATS:
            raise InputValidationError(
                "The decoded container is not a supported lossless format."
            )
        expected_format = {".wav": "WAV", ".flac": "FLAC"}[source.suffix.lower()]
        if source_format != expected_format:
            raise InputValidationError(
                "The filename extension does not match the decoded container."
            )
        if not _is_lossless_subtype(info.subtype):
            raise InputValidationError(
                "The decoded audio subtype is not lossless PCM or floating point."
            )
        if info.channels != REQUIRED_CHANNELS:
            raise InputValidationError("Mixing v1 requires exactly two audio channels.")
        if info.samplerate < MIN_SAMPLE_RATE:
            raise InputValidationError(
                "Mixing v1 requires a sample rate of at least 44.1 kHz."
            )
        duration = float(info.frames / info.samplerate) if info.samplerate else 0.0
        if duration < MIN_DURATION_SECONDS or duration > MAX_DURATION_SECONDS:
            raise InputValidationError(
                "Mixing v1 accepts tracks from 30 seconds through 10 minutes."
            )

        try:
            samples, sample_rate = sf.read(source, dtype="float32", always_2d=True)
        except (RuntimeError, TypeError) as exc:
            raise DecoderError(
                "The audio source failed during full-frame decoding."
            ) from exc

        if samples.shape != (info.frames, REQUIRED_CHANNELS):
            raise DecoderError(
                "Decoded frame or channel counts do not match the container metadata."
            )
        if samples.size == 0 or not np.isfinite(samples).all():
            raise DecoderError("Decoded audio is empty or contains non-finite samples.")

        return AudioData(
            samples=np.ascontiguousarray(samples, dtype=np.float32),
            sample_rate=int(sample_rate),
            source_format=source_format,
            subtype=info.subtype,
            duration_seconds=duration,
            content_sha256=_sha256_file(source),
        )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_lossless_subtype(subtype: str) -> bool:
    normalized = subtype.upper()
    return normalized.startswith("PCM_") or normalized in {"FLOAT", "DOUBLE"}
