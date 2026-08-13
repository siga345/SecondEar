from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from secondear_analysis.audio import SoundFileDecoder
from secondear_analysis.errors import DecoderError, InputValidationError


def test_decodes_lossless_wav(stereo_wav: Path) -> None:
    audio = SoundFileDecoder().decode(stereo_wav)

    assert audio.source_format == "WAV"
    assert audio.subtype == "PCM_24"
    assert audio.sample_rate == 44_100
    assert audio.channels == 2
    assert audio.duration_seconds == pytest.approx(30.0)
    assert len(audio.content_sha256) == 64


def test_decodes_lossless_flac(stereo_flac: Path) -> None:
    audio = SoundFileDecoder().decode(stereo_flac)
    assert audio.source_format == "FLAC"
    assert audio.channels == 2


@pytest.mark.parametrize("duration", [29.999, 600.001])
def test_rejects_duration_outside_30_seconds_through_10_minutes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, duration: float
) -> None:
    source = tmp_path / "track.wav"
    source.write_bytes(b"fixture")
    frames = int(duration * 44_100)
    monkeypatch.setattr(
        "secondear_analysis.audio.sf.info",
        lambda _: SimpleNamespace(
            format="WAV",
            subtype="PCM_24",
            channels=2,
            samplerate=44_100,
            frames=frames,
        ),
    )

    with pytest.raises(InputValidationError, match="30 seconds through 10 minutes"):
        SoundFileDecoder().decode(source)


def test_rejects_mismatched_extension(stereo_flac: Path, tmp_path: Path) -> None:
    disguised = tmp_path / "disguised.wav"
    disguised.write_bytes(stereo_flac.read_bytes())

    with pytest.raises(InputValidationError, match="extension"):
        SoundFileDecoder().decode(disguised)


def test_rejects_damaged_audio_container(tmp_path: Path) -> None:
    damaged = tmp_path / "damaged.wav"
    damaged.write_bytes(b"this is not a wave container")

    with pytest.raises(DecoderError, match="could not be decoded"):
        SoundFileDecoder().decode(damaged)


@pytest.mark.parametrize(
    ("channels", "sample_rate", "subtype", "message"),
    [
        (1, 44_100, "PCM_24", "exactly two"),
        (3, 44_100, "PCM_24", "exactly two"),
        (2, 22_050, "PCM_24", "44.1 kHz"),
        (2, 44_100, "ULAW", "lossless"),
    ],
)
def test_rejects_inapplicable_container_properties(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    channels: int,
    sample_rate: int,
    subtype: str,
    message: str,
) -> None:
    source = tmp_path / "track.wav"
    source.write_bytes(b"fixture")
    monkeypatch.setattr(
        "secondear_analysis.audio.sf.info",
        lambda _: SimpleNamespace(
            format="WAV",
            subtype=subtype,
            channels=channels,
            samplerate=sample_rate,
            frames=sample_rate * 30,
        ),
    )

    with pytest.raises(InputValidationError, match=message):
        SoundFileDecoder().decode(source)
