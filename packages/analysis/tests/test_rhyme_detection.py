from __future__ import annotations

import pytest
from secondear_analysis.dictionaries import parse_arpabet
from secondear_analysis.domain import RhymePosition, RhymeType
from secondear_analysis.rhyme import SCORING_TYPES, detect_rhymes
from secondear_analysis.text import parse_lyrics


def _detect(lyrics: str, notation_by_word: dict[str, str]):
    document = parse_lyrics(lyrics)
    pronunciations = {
        token.id: parse_arpabet(notation_by_word[token.normalized].split())
        for section in document.sections
        for line in section.lines
        for token in line.tokens
    }
    return detect_rhymes(document, pronunciations, notation_by_word.keys())


def test_exact_identity_homophone_and_non_rhyme_classification() -> None:
    exact = _detect("night\nlight", {"night": "N AY1 T", "light": "L AY1 T"})
    assert any(pair.rhyme_type is RhymeType.EXACT for pair in exact.pairs)

    identity = _detect("night\nnight", {"night": "N AY1 T"})
    assert any(
        pair.rhyme_type is RhymeType.IDENTITY and pair.same_word
        for pair in identity.pairs
    )

    homophone = _detect(
        "night\nnite",
        {"night": "N AY1 T", "nite": "N AY1 T"},
    )
    assert any(
        pair.rhyme_type is RhymeType.IDENTITY and pair.homophone
        for pair in homophone.pairs
    )

    unrelated = _detect("night\nblue", {"night": "N AY1 T", "blue": "B L UW1"})
    assert not any(pair.rhyme_type in SCORING_TYPES for pair in unrelated.pairs)


def test_same_onset_without_full_identity_is_near() -> None:
    result = _detect(
        "alight\nlight",
        {"alight": "AH0 L AY1 T", "light": "L AY1 T"},
    )

    assert any(pair.rhyme_type is RhymeType.NEAR for pair in result.pairs)
    assert not any(pair.rhyme_type is RhymeType.IDENTITY for pair in result.pairs)


def test_assonance_and_consonance_remain_non_scoring_evidence() -> None:
    assonance = _detect(
        "cat\ncamp",
        {"cat": "K AE1 T", "camp": "K AE1 M P"},
    )
    consonance = _detect(
        "beat\nboat",
        {"beat": "B IY1 T", "boat": "B OW1 T"},
    )

    assert any(pair.rhyme_type is RhymeType.ASSONANCE for pair in assonance.pairs)
    assert any(pair.rhyme_type is RhymeType.CONSONANCE for pair in consonance.pairs)
    assert assonance.accepted_pair_count == 0
    assert consonance.accepted_pair_count == 0


def test_internal_multiword_and_multisyllabic_evidence() -> None:
    internal = _detect(
        "night light",
        {"night": "N AY1 T", "light": "L AY1 T"},
    )
    assert any(pair.position is RhymePosition.INTERNAL for pair in internal.pairs)

    construction = _detect(
        "make a\ntake a",
        {
            "make": "M EY1 K",
            "take": "T EY1 K",
            "a": "AH0",
        },
    )
    assert any(pair.multiword and pair.multisyllabic for pair in construction.pairs)


def test_terminal_scoring_pairs_do_not_reuse_token_occurrences() -> None:
    result = _detect(
        "night\nlight\nbright\nright",
        {
            "night": "N AY1 T",
            "light": "L AY1 T",
            "bright": "B R AY1 T",
            "right": "R AY1 T",
        },
    )
    terminal_pairs = [pair for pair in result.pairs if pair.position is RhymePosition.LINE_END]
    occurrence_by_id = {occurrence.id: occurrence for occurrence in result.occurrences}
    used: set[str] = set()
    for pair in terminal_pairs:
        token_ids = set(occurrence_by_id[pair.left_occurrence_id].token_ids)
        token_ids.update(occurrence_by_id[pair.right_occurrence_id].token_ids)
        assert not token_ids & used
        used.update(token_ids)
    assert result.schemes[0].pattern == ("A", "A", "A", "A")


@pytest.mark.parametrize(
    ("lyrics", "expected"),
    [
        ("night\nlight\nblue\ntrue", ("A", "A", "B", "B")),
        ("night\nblue\nlight\ntrue", ("A", "B", "A", "B")),
        ("night\nblue\ntrue\nlight", ("A", "B", "B", "A")),
    ],
)
def test_named_four_line_scheme_patterns(lyrics: str, expected: tuple[str, ...]) -> None:
    result = _detect(
        lyrics,
        {
            "night": "N AY1 T",
            "light": "L AY1 T",
            "blue": "B L UW1",
            "true": "T R UW1",
        },
    )

    assert result.schemes[0].pattern == expected
