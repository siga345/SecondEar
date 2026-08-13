"""Typed domain contracts for English rhyme analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

type Scalar = str | int | float | bool


class LanguageProfile(StrEnum):
    """Supported pronunciation profiles."""

    EN_US = "en-US"
    EN_GB = "en-GB"


class PrimaryTag(StrEnum):
    """Genre profiles used by formula version 0.1."""

    RAP = "rap"
    POP = "pop"
    RNB = "rnb"
    ROCK = "rock"
    COUNTRY = "country"
    ELECTRONIC = "electronic"


class AnalysisStatus(StrEnum):
    """Applicability state of a rhyme result."""

    EVALUATED = "evaluated"
    NEEDS_PRONUNCIATION_REVIEW = "needs_pronunciation_review"
    INSUFFICIENT_DATA = "insufficient_data"


class RhymeType(StrEnum):
    """Evidence-backed phonetic relationship between two occurrences."""

    EXACT = "exact"
    NEAR = "near"
    IDENTITY = "identity"
    ASSONANCE = "assonance"
    CONSONANCE = "consonance"


class RhymePosition(StrEnum):
    """Position of a relationship in the submitted lines."""

    LINE_END = "line_end"
    INTERNAL = "internal"


@dataclass(frozen=True, slots=True)
class PronunciationOverride:
    """Caller-selected pronunciation in the notation native to a profile.

    ``target`` is either a token occurrence identifier returned by an earlier
    analysis or a normalized word applied to every matching occurrence.
    """

    target: str
    pronunciation: str


@dataclass(frozen=True, slots=True)
class RhymeAnalysisRequest:
    """Input accepted by the framework-independent analyzer."""

    lyrics: str
    language_profile: LanguageProfile
    primary_tag: PrimaryTag
    pronunciation_overrides: tuple[PronunciationOverride, ...] = ()
    source_reference: str | None = None


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """Coordinates in the exact submitted lyrics string."""

    line_index: int
    start: int
    end: int


@dataclass(frozen=True, slots=True)
class PronunciationIssue:
    """A token whose pronunciation requires caller review."""

    token_id: str
    token: str
    normalized: str
    span: SourceSpan
    reason: str
    choices: tuple[str, ...]
    blocks_score: bool


@dataclass(frozen=True, slots=True)
class AnalyzedLine:
    """One unique analyzed lyric line with coordinates in the submitted text."""

    section_index: int
    line_index: int
    span: SourceSpan


@dataclass(frozen=True, slots=True)
class RhymeOccurrence:
    """A word or phrase participating in phonetic evidence."""

    id: str
    text: str
    normalized_tokens: tuple[str, ...]
    token_ids: tuple[str, ...]
    phonemes: tuple[str, ...]
    rhyme_zone: tuple[str, ...]
    syllable_count: int
    section_index: int
    line_index: int
    span: SourceSpan
    is_line_ending: bool


@dataclass(frozen=True, slots=True)
class RhymePair:
    """A classified relationship and the evidence used to classify it."""

    id: str
    left_occurrence_id: str
    right_occurrence_id: str
    rhyme_type: RhymeType
    position: RhymePosition
    similarity: float
    nucleus_similarity: float
    multisyllabic: bool
    multiword: bool
    same_word: bool
    lemma_comparable: bool
    same_lemma: bool
    homophone: bool


@dataclass(frozen=True, slots=True)
class RhymeFamily:
    """Complete-link family used in line-ending schemes."""

    label: str
    occurrence_ids: tuple[str, ...]
    line_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class RhymeChain:
    """Ordered occurrence sequence within one complete-link family."""

    id: str
    family_label: str
    occurrence_ids: tuple[str, ...]
    line_indices: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class SectionScheme:
    """Line-ending family labels for one unique section."""

    section_index: int
    label: str
    occurrence_count: int
    pattern: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Metric:
    """Traceable analytical value."""

    key: str
    value: Scalar
    unit: str | None
    evidence_type: str
    analyzer: str = "english_rhymes"
    analyzer_version: str = "0.1.0"


@dataclass(frozen=True, slots=True)
class Finding:
    """Neutral conclusion linked to one or more metrics."""

    id: str
    title: str
    description: str
    evidence: tuple[str, ...]
    severity: str


@dataclass(frozen=True, slots=True)
class AnalysisVersions:
    """Reproducibility identifiers for every behavior-changing resource."""

    analysis_version: str
    analyzer_version: str
    formula_version: str
    profile_version: str
    phoneme_features_version: str
    morphology_version: str
    dictionary_name: str
    dictionary_version: str
    dictionary_sha256: str


@dataclass(frozen=True, slots=True)
class InputSummary:
    """Counts and coverage used by applicability and confidence."""

    total_sections: int
    unique_sections: int
    repeated_sections: int
    total_lines: int
    unique_lines: int
    lexical_tokens: int
    resolved_tokens: int
    syllables: int
    line_endings: int
    resolved_line_endings: int
    pronunciation_coverage: float
    line_ending_coverage: float


@dataclass(frozen=True, slots=True)
class RhymeAnalysisResult:
    """Complete, serializable result for the Rhymes criterion."""

    criterion: str
    status: AnalysisStatus
    score: float | None
    scale_max: int
    confidence: float
    language_profile: LanguageProfile
    primary_tag: PrimaryTag
    source_reference: str | None
    versions: AnalysisVersions
    input_summary: InputSummary
    pronunciation_issues: tuple[PronunciationIssue, ...]
    lines: tuple[AnalyzedLine, ...]
    occurrences: tuple[RhymeOccurrence, ...]
    pairs: tuple[RhymePair, ...]
    families: tuple[RhymeFamily, ...]
    chains: tuple[RhymeChain, ...]
    schemes: tuple[SectionScheme, ...]
    metrics: tuple[Metric, ...]
    subscores: dict[str, float]
    findings: tuple[Finding, ...]
    limitations: tuple[str, ...] = field(default_factory=tuple)
