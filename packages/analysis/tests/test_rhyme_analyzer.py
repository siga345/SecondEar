from __future__ import annotations

from secondear_analysis import (
    LanguageProfile,
    PrimaryTag,
    PronunciationOverride,
    RhymeAnalysisRequest,
    RhymeAnalysisStatus,
    analyze_rhymes,
)
from secondear_analysis.domain import RhymeType

LONG_LYRICS = """[Verse]
We carry every story and follow the light
We answer every warning and travel at night
We gather all the pieces and make the words bright
We measure every cadence until it is right

[Chorus]
We stand beside the river with maps in our hand
We plan another passage across the open land
We mark another measure exactly as planned
We start another chapter and build where we stand
"""


def test_analysis_is_deterministic_and_traceable() -> None:
    request = RhymeAnalysisRequest(LONG_LYRICS, LanguageProfile.EN_US, PrimaryTag.POP)
    first = analyze_rhymes(request)
    second = analyze_rhymes(request)

    assert first == second
    assert first.status is RhymeAnalysisStatus.EVALUATED
    assert first.score is not None and 1.0 <= first.score <= 10.0
    assert first.versions.formula_version == "english-rhymes-score-0.1.0"
    assert first.input_summary.unique_lines == 8
    assert any(pair.rhyme_type is RhymeType.EXACT for pair in first.pairs)
    assert all(0.0 <= pair.similarity <= 1.0 for pair in first.pairs)


def test_unresolved_line_ending_requires_review_then_override_unblocks_score() -> None:
    lyrics = LONG_LYRICS.replace("stand\n", "glorptastic\n", 1)
    initial = analyze_rhymes(
        RhymeAnalysisRequest(lyrics, LanguageProfile.EN_US, PrimaryTag.ROCK)
    )
    assert initial.status is RhymeAnalysisStatus.NEEDS_PRONUNCIATION_REVIEW
    issue = next(issue for issue in initial.pronunciation_issues if issue.blocks_score)
    assert issue.normalized == "glorptastic"

    reviewed = analyze_rhymes(
        RhymeAnalysisRequest(
            lyrics,
            LanguageProfile.EN_US,
            PrimaryTag.ROCK,
            (PronunciationOverride(issue.token_id, "G L AO0 R P T AE1 S T IH0 K"),),
        )
    )
    assert reviewed.status is RhymeAnalysisStatus.EVALUATED
    assert reviewed.score is not None


def test_short_text_is_insufficient_data_not_zero() -> None:
    result = analyze_rhymes(
        RhymeAnalysisRequest("night light", LanguageProfile.EN_US, PrimaryTag.RAP)
    )
    assert result.status is RhymeAnalysisStatus.INSUFFICIENT_DATA
    assert result.score is None


def test_known_inflection_is_reported_only_as_diversity_evidence() -> None:
    lyrics = """We run through the city and build a nation
We keep every measure and study the nations
We write every message beside the color blue
We count every footstep beside the color red
We run through the valley and guide a nation
We keep every signal and map all the nations
We write every marker beside the color green
We count every pattern beside the color gold
"""
    result = analyze_rhymes(
        RhymeAnalysisRequest(lyrics, LanguageProfile.EN_US, PrimaryTag.RAP)
    )

    assert any(pair.same_lemma for pair in result.pairs)
    metrics = {metric.key: metric.value for metric in result.metrics}
    assert metrics["same_lemma_rhyme_rate"] > 0
    assert result.versions.morphology_version == "english-conservative-morphology-0.1.0"


def test_dialect_changes_spa_car_relation() -> None:
    lyrics = """I take the road and drive the car
I cross the town to reach the spa
I read the map beneath a star
I leave the room with one hurrah
I take the road and drive the car
I cross the town to reach the spa
I read the map beneath a star
I leave the room with one hurrah
"""
    us = analyze_rhymes(
        RhymeAnalysisRequest(lyrics, LanguageProfile.EN_US, PrimaryTag.POP)
    )
    gb = analyze_rhymes(
        RhymeAnalysisRequest(lyrics, LanguageProfile.EN_GB, PrimaryTag.POP)
    )

    us_exact = sum(pair.rhyme_type is RhymeType.EXACT for pair in us.pairs)
    gb_exact = sum(pair.rhyme_type is RhymeType.EXACT for pair in gb.pairs)
    assert gb_exact > us_exact
