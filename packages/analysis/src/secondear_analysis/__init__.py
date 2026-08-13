"""Framework-independent SecondEar analysis engine."""

from .domain import (
    AnalysisStatus as RhymeAnalysisStatus,
    LanguageProfile,
    PrimaryTag,
    PronunciationOverride,
    RhymeAnalysisRequest,
    RhymeAnalysisResult,
)
from .models import AnalysisStatus as MixingAnalysisStatus
from .models import MixingResult, PrimaryGenre
from .rhyme_analyzer import analyze_rhymes

__all__ = [
    "LanguageProfile",
    "MixingAnalysisStatus",
    "MixingResult",
    "PrimaryGenre",
    "PrimaryTag",
    "PronunciationOverride",
    "RhymeAnalysisRequest",
    "RhymeAnalysisResult",
    "RhymeAnalysisStatus",
    "analyze_rhymes",
]

try:
    from .pipeline import analyze_mixing
except ModuleNotFoundError:
    # Mixing can be installed as an optional analysis slice while its native
    # dependencies are unavailable. Rhymes has no native runtime dependency.
    analyze_mixing = None  # type: ignore[assignment]
else:
    __all__.append("analyze_mixing")

__version__ = "0.1.0"
