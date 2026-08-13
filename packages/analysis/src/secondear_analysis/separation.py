"""Bounded source-separation adapters for element-balance evidence."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib import metadata
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from .audio import AudioData
from .config import (
    MAX_SEPARATION_RESIDUAL_DB,
    SEPARATION_CONFIDENCE_CAP,
    STEM_NAMES,
)
from .dsp import amplitude_to_db
from .errors import SeparationError
from .models import SeparatorIdentity


@dataclass(frozen=True, slots=True)
class StemSet:
    """Estimated stereo roles and the mixture used by the separator."""

    sources: dict[str, NDArray[np.float32]]
    mixture: NDArray[np.float32]
    sample_rate: int
    identity: SeparatorIdentity
    residual_db: float
    confidence: float


class SourceSeparator(Protocol):
    def separate(self, audio: AudioData) -> StemSet:
        """Estimate the four Mixing v1 source roles."""


class DemucsSeparator:
    """CPU-only deterministic adapter for the four-role htdemucs_ft model."""

    def __init__(self, model_name: str = "htdemucs_ft") -> None:
        self.model_name = model_name
        self._model = None
        self._identity: SeparatorIdentity | None = None

    def separate(self, audio: AudioData) -> StemSet:
        try:
            import torch
            import torchaudio
            from demucs.apply import apply_model
            from demucs.audio import convert_audio
            from demucs.pretrained import get_model
        except ImportError as exc:
            raise SeparationError(
                "Demucs dependencies are not installed; install the separation extra."
            ) from exc

        if self._model is None:
            try:
                self._model = get_model(self.model_name)
                self._model.to("cpu")
                self._model.eval()
            # Model downloads and Torch initialization errors become domain evidence.
            except Exception as exc:
                raise SeparationError(
                    "The configured Demucs model could not be loaded."
                ) from exc
            self._identity = SeparatorIdentity(
                implementation="demucs",
                implementation_version=_package_version("demucs"),
                model=self.model_name,
                model_checksum=_state_dict_checksum(self._model),
                torch_version=str(torch.__version__),
                torchaudio_version=str(torchaudio.__version__),
            )

        model = self._model
        waveform = torch.from_numpy(np.ascontiguousarray(audio.samples.T)).float()
        try:
            converted = convert_audio(
                waveform,
                audio.sample_rate,
                model.samplerate,
                model.audio_channels,
            )
            mixture = converted.clone()
            reference = converted.mean(0)
            mean = reference.mean()
            std = reference.std().clamp_min(1e-8)
            normalized = (converted - mean) / std
            with torch.inference_mode():
                estimates = apply_model(
                    model,
                    normalized[None],
                    device="cpu",
                    shifts=1,
                    split=True,
                    overlap=0.25,
                    progress=False,
                )[0]
            estimates = estimates * std + mean
        except Exception as exc:
            raise SeparationError(
                "Demucs failed while estimating source roles."
            ) from exc

        model_sources = tuple(model.sources)
        if set(model_sources) != set(STEM_NAMES):
            raise SeparationError(
                "The configured model does not expose the four required roles."
            )
        source_arrays = {
            name: np.ascontiguousarray(
                estimates[model_sources.index(name)].cpu().numpy().T, dtype=np.float32
            )
            for name in STEM_NAMES
        }
        mixture_array = np.ascontiguousarray(mixture.cpu().numpy().T, dtype=np.float32)
        residual = mixture_array - sum(source_arrays.values())
        residual_rms = float(np.sqrt(np.mean(np.square(residual, dtype=np.float64))))
        mixture_rms = float(
            np.sqrt(np.mean(np.square(mixture_array, dtype=np.float64)))
        )
        residual_db = amplitude_to_db(residual_rms / max(mixture_rms, 1e-12))
        if not all(np.isfinite(source).all() for source in source_arrays.values()):
            raise SeparationError("Demucs returned non-finite source estimates.")
        if any(
            source.shape != mixture_array.shape for source in source_arrays.values()
        ):
            raise SeparationError("Demucs returned inconsistent source dimensions.")
        if residual_db > MAX_SEPARATION_RESIDUAL_DB:
            raise SeparationError(
                "Source reconstruction residual exceeds the Mixing v1 reliability threshold."
            )
        assert self._identity is not None
        return StemSet(
            sources=source_arrays,
            mixture=mixture_array,
            sample_rate=int(model.samplerate),
            identity=self._identity,
            residual_db=residual_db,
            confidence=SEPARATION_CONFIDENCE_CAP,
        )


def _package_version(package: str) -> str:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return "unknown"


def _state_dict_checksum(model: object) -> str:
    """Hash actual model parameters instead of trusting a mutable model name."""

    digest = hashlib.sha256()
    for key, tensor in sorted(model.state_dict().items()):  # type: ignore[attr-defined]
        array = tensor.detach().cpu().contiguous().numpy()
        digest.update(key.encode("utf-8"))
        digest.update(str(array.dtype).encode("ascii"))
        digest.update(str(array.shape).encode("ascii"))
        digest.update(array.tobytes())
    return digest.hexdigest()
