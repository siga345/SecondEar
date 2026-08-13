"""Orchestration for the text-only English Rhymes criterion."""

from __future__ import annotations

from secondear_analysis.dictionaries import (
    Pronunciation,
    PronunciationLexicon,
    load_default_lexicon,
)
from secondear_analysis.domain import (
    AnalysisStatus,
    AnalysisVersions,
    AnalyzedLine,
    Finding,
    InputSummary,
    Metric,
    PronunciationIssue,
    RhymeAnalysisRequest,
    RhymeAnalysisResult,
)
from secondear_analysis.morphology import MORPHOLOGY_VERSION
from secondear_analysis.phonetics import FEATURES_VERSION
from secondear_analysis.rhyme import detect_rhymes
from secondear_analysis.rhyme_scoring import (
    FORMULA_VERSION,
    PROFILE_VERSION,
    calculate_score,
)
from secondear_analysis.text import LyricsDocument, Token, parse_lyrics

ANALYSIS_VERSION = "rhymes-analysis-0.1.0"
ANALYZER_VERSION = "english-rhymes-0.1.0"
MAX_LYRICS_BYTES = 256 * 1024
MIN_UNIQUE_LINES = 8
MIN_LEXICAL_TOKENS = 40
MIN_PRONUNCIATION_COVERAGE = 0.85
MIN_LINE_ENDING_COVERAGE = 0.90


def _all_tokens(document: LyricsDocument) -> list[Token]:
    return [token for section in document.sections for line in section.lines for token in line.tokens]


def _override_map(request: RhymeAnalysisRequest) -> dict[str, str]:
    return {override.target.casefold(): override.pronunciation for override in request.pronunciation_overrides}


def _resolve(
    document: LyricsDocument,
    request: RhymeAnalysisRequest,
    lexicon: PronunciationLexicon,
) -> tuple[dict[str, Pronunciation], tuple[PronunciationIssue, ...], float]:
    overrides = _override_map(request)
    resolved: dict[str, Pronunciation] = {}
    issues: list[PronunciationIssue] = []
    certainty_total = 0.0
    tokens = _all_tokens(document)
    for token in tokens:
        override_value = overrides.get(token.id.casefold()) or overrides.get(token.normalized)
        if override_value is not None:
            try:
                resolved[token.id] = lexicon.parse_override(override_value)
                certainty_total += 0.95
            except ValueError as error:
                issues.append(
                    PronunciationIssue(
                        token_id=token.id,
                        token=token.text,
                        normalized=token.normalized,
                        span=token.span,
                        reason=f"invalid_override: {error}",
                        choices=(),
                        blocks_score=token.is_line_ending,
                    )
                )
            continue
        choices = lexicon.lookup(token.normalized)
        if not choices:
            issues.append(
                PronunciationIssue(
                    token_id=token.id,
                    token=token.text,
                    normalized=token.normalized,
                    span=token.span,
                    reason="out_of_vocabulary",
                    choices=(),
                    blocks_score=token.is_line_ending,
                )
            )
            continue
        resolved[token.id] = choices[0]
        if len(choices) == 1:
            certainty_total += 1.0
        else:
            certainty_total += 0.5
            issues.append(
                PronunciationIssue(
                    token_id=token.id,
                    token=token.text,
                    normalized=token.normalized,
                    span=token.span,
                    reason="ambiguous_pronunciation",
                    choices=tuple(choice.notation for choice in choices),
                    blocks_score=token.is_line_ending,
                )
            )
    certainty = certainty_total / len(tokens) if tokens else 0.0
    return resolved, tuple(issues), certainty


def _findings(score: float | None, metrics: tuple[Metric, ...]) -> tuple[Finding, ...]:
    values = {metric.key: metric.value for metric in metrics}
    findings: list[Finding] = []
    if values.get("accepted_rhyme_pair_count", 0) == 0:
        findings.append(
            Finding(
                id="no_scoring_rhyme_relations",
                title="No scoring rhyme relations detected",
                description=(
                    "No exact, near, or identity relation passed the published thresholds in the "
                    "analyzable text."
                ),
                evidence=("accepted_rhyme_pair_count",),
                severity="notice",
            )
        )
    identity_rate = values.get("identity_rhyme_rate")
    if isinstance(identity_rate, float) and identity_rate >= 0.4:
        findings.append(
            Finding(
                id="high_identity_rhyme_rate",
                title="High identity-rhyme rate",
                description=(
                    "At least 40% of scoring relations reuse the same full pronunciation; this is "
                    "reported inside the diversity component."
                ),
                evidence=("identity_rhyme_rate",),
                severity="notice",
            )
        )
    if score is not None and score >= 8.0:
        findings.append(
            Finding(
                id="strong_profile_relative_construction",
                title="Strong profile-relative rhyme construction",
                description=(
                    "The versioned formula places the submitted construction in its strong range "
                    "for the selected seed genre profile."
                ),
                evidence=("formula_index",),
                severity="info",
            )
        )
    return tuple(findings)


def analyze_rhymes(
    request: RhymeAnalysisRequest,
    *,
    lexicon: PronunciationLexicon | None = None,
) -> RhymeAnalysisResult:
    """Analyze submitted English lyrics without persistence or network calls."""

    if len(request.lyrics.encode("utf-8")) > MAX_LYRICS_BYTES:
        raise ValueError(f"Lyrics exceed the {MAX_LYRICS_BYTES}-byte limit")
    active_lexicon = lexicon or load_default_lexicon(request.language_profile)
    if active_lexicon.profile is not request.language_profile:
        raise ValueError("The pronunciation lexicon does not match the requested language profile")
    document = parse_lyrics(request.lyrics)
    tokens = _all_tokens(document)
    resolved, issues, pronunciation_certainty = _resolve(document, request, active_lexicon)
    line_end_tokens = [token for token in tokens if token.is_line_ending]
    resolved_line_endings = sum(token.id in resolved for token in line_end_tokens)
    pronunciation_coverage = len(resolved) / len(tokens) if tokens else 0.0
    line_ending_coverage = (
        resolved_line_endings / len(line_end_tokens) if line_end_tokens else 0.0
    )
    syllables = sum(
        phone.is_vowel for pronunciation in resolved.values() for phone in pronunciation.phones
    )
    unique_lines = sum(len(section.lines) for section in document.sections)
    summary = InputSummary(
        total_sections=document.total_sections,
        unique_sections=len(document.sections),
        repeated_sections=document.repeated_sections,
        total_lines=document.total_lines,
        unique_lines=unique_lines,
        lexical_tokens=len(tokens),
        resolved_tokens=len(resolved),
        syllables=syllables,
        line_endings=len(line_end_tokens),
        resolved_line_endings=resolved_line_endings,
        pronunciation_coverage=round(pronunciation_coverage, 4),
        line_ending_coverage=round(line_ending_coverage, 4),
    )
    detection = detect_rhymes(document, resolved, active_lexicon.entries.keys())
    score_result = calculate_score(detection, request.primary_tag, len(tokens), unique_lines)
    blocking_review = any(issue.blocks_score for issue in issues)
    enough_data = (
        unique_lines >= MIN_UNIQUE_LINES
        and len(tokens) >= MIN_LEXICAL_TOKENS
        and pronunciation_coverage >= MIN_PRONUNCIATION_COVERAGE
        and line_ending_coverage >= MIN_LINE_ENDING_COVERAGE
    )
    if blocking_review:
        status = AnalysisStatus.NEEDS_PRONUNCIATION_REVIEW
        score = None
    elif not enough_data:
        status = AnalysisStatus.INSUFFICIENT_DATA
        score = None
    else:
        status = AnalysisStatus.EVALUATED
        score = score_result.score
    section_certainty = 0.9 if len(document.sections) > 1 else 0.75 if document.sections else 0.0
    confidence = round(
        0.45 * pronunciation_coverage
        + 0.25 * line_ending_coverage
        + 0.15 * pronunciation_certainty
        + 0.15 * section_certainty,
        4,
    )
    coverage_metrics = (
        Metric("lexical_token_count", len(tokens), "tokens", "measured"),
        Metric("syllable_count", syllables, "syllables", "estimated"),
        Metric("pronunciation_coverage", round(pronunciation_coverage, 4), "ratio", "derived"),
        Metric("line_ending_coverage", round(line_ending_coverage, 4), "ratio", "derived"),
        Metric("repeated_section_count", document.repeated_sections, "sections", "measured"),
    )
    metrics = coverage_metrics + score_result.metrics
    limitations = [
        "Dictionary pronunciation is not evidence of the performed pronunciation.",
        "Assonance and consonance are reported as evidence but do not contribute to formula 0.1.",
        "Seed profile anchors require calibration against the owner corpus.",
    ]
    if request.language_profile.value == "en-GB":
        limitations.append(
            "The en-GB profile represents Britfone Standard Southern British/RP, not all UK accents."
        )
    return RhymeAnalysisResult(
        criterion="rhymes",
        status=status,
        score=score,
        scale_max=10,
        confidence=confidence,
        language_profile=request.language_profile,
        primary_tag=request.primary_tag,
        source_reference=request.source_reference,
        versions=AnalysisVersions(
            analysis_version=ANALYSIS_VERSION,
            analyzer_version=ANALYZER_VERSION,
            formula_version=FORMULA_VERSION,
            profile_version=PROFILE_VERSION,
            phoneme_features_version=FEATURES_VERSION,
            morphology_version=MORPHOLOGY_VERSION,
            dictionary_name=active_lexicon.name,
            dictionary_version=active_lexicon.version,
            dictionary_sha256=active_lexicon.sha256,
        ),
        input_summary=summary,
        pronunciation_issues=issues,
        lines=tuple(
            AnalyzedLine(
                section_index=section.index,
                line_index=line.line_index,
                span=line.span,
            )
            for section in document.sections
            for line in section.lines
        ),
        occurrences=detection.occurrences,
        pairs=detection.pairs,
        families=detection.families,
        chains=detection.chains,
        schemes=detection.schemes,
        metrics=metrics,
        subscores=score_result.subscores,
        findings=_findings(score, metrics),
        limitations=tuple(limitations),
    )
