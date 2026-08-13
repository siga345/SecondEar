"""HTTP schemas kept separate from the analysis domain models."""

from __future__ import annotations

from dataclasses import asdict

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from secondear_analysis.domain import (
    AnalysisStatus,
    LanguageProfile,
    PrimaryTag,
    RhymeAnalysisResult,
    RhymePosition,
    RhymeType,
)


class PronunciationOverrideInput(BaseModel):
    target: str = Field(min_length=1, max_length=128)
    pronunciation: str = Field(min_length=1, max_length=512)


class RhymeAnalysisInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lyrics: str = Field(min_length=1, max_length=262_144)
    language_profile: LanguageProfile
    primary_tag: PrimaryTag
    pronunciation_overrides: list[PronunciationOverrideInput] = Field(
        default_factory=list, max_length=512
    )
    source_reference: str | None = Field(default=None, max_length=2_048)


class SourceSpanOutput(BaseModel):
    line_index: int
    start: int
    end: int


class PronunciationIssueOutput(BaseModel):
    token_id: str
    token: str
    normalized: str
    span: SourceSpanOutput
    reason: str
    choices: list[str]
    blocks_score: bool


class AnalyzedLineOutput(BaseModel):
    section_index: int
    line_index: int
    span: SourceSpanOutput


class RhymeOccurrenceOutput(BaseModel):
    id: str
    text: str
    normalized_tokens: list[str]
    token_ids: list[str]
    phonemes: list[str]
    rhyme_zone: list[str]
    syllable_count: int
    section_index: int
    line_index: int
    span: SourceSpanOutput
    is_line_ending: bool


class RhymePairOutput(BaseModel):
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


class RhymeFamilyOutput(BaseModel):
    label: str
    occurrence_ids: list[str]
    line_indices: list[int]


class RhymeChainOutput(BaseModel):
    id: str
    family_label: str
    occurrence_ids: list[str]
    line_indices: list[int]


class SectionSchemeOutput(BaseModel):
    section_index: int
    label: str
    occurrence_count: int
    pattern: list[str]


class MetricOutput(BaseModel):
    key: str
    value: str | int | float | bool
    unit: str | None
    evidence_type: str
    analyzer: str
    analyzer_version: str


class FindingOutput(BaseModel):
    id: str
    title: str
    description: str
    evidence: list[str]
    severity: str


class VersionsOutput(BaseModel):
    analysis_version: str
    analyzer_version: str
    formula_version: str
    profile_version: str
    phoneme_features_version: str
    morphology_version: str
    dictionary_name: str
    dictionary_version: str
    dictionary_sha256: str


class InputSummaryOutput(BaseModel):
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


class RhymeAnalysisOutput(BaseModel):
    criterion: str
    status: AnalysisStatus
    score: float | None
    scale_max: int
    confidence: float
    language_profile: LanguageProfile
    primary_tag: PrimaryTag
    source_reference: str | None
    versions: VersionsOutput
    input_summary: InputSummaryOutput
    pronunciation_issues: list[PronunciationIssueOutput]
    lines: list[AnalyzedLineOutput]
    occurrences: list[RhymeOccurrenceOutput]
    pairs: list[RhymePairOutput]
    families: list[RhymeFamilyOutput]
    chains: list[RhymeChainOutput]
    schemes: list[SectionSchemeOutput]
    metrics: list[MetricOutput]
    subscores: dict[str, float]
    findings: list[FindingOutput]
    limitations: list[str]


_RESULT_ADAPTER = TypeAdapter(RhymeAnalysisOutput)


def result_to_output(result: RhymeAnalysisResult) -> RhymeAnalysisOutput:
    """Map the domain result without exposing domain classes to FastAPI."""

    return _RESULT_ADAPTER.validate_python(asdict(result))
