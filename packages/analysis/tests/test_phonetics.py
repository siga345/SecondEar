from __future__ import annotations

import math

import pytest
from secondear_analysis.dictionaries import parse_arpabet
from secondear_analysis.phonetics import (
    phone_similarity,
    rhyme_zone,
    sequence_similarity,
)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (["N", "AY1", "T"], ["L", "AY1", "T"]),
        (["HH", "AE1", "N", "D", "Z"], ["P", "L", "AE1", "N", "Z"]),
        (["F", "AY1", "R"], ["HH", "AY1", "ER0"]),
    ],
)
def test_sequence_similarity_is_symmetric_finite_and_bounded(
    left: list[str], right: list[str]
) -> None:
    left_zone = rhyme_zone(parse_arpabet(left).phones)
    right_zone = rhyme_zone(parse_arpabet(right).phones)
    forward = sequence_similarity(left_zone, right_zone)
    backward = sequence_similarity(right_zone, left_zone)

    assert forward == pytest.approx(backward)
    assert 0.0 <= forward <= 1.0
    assert math.isfinite(forward)


def test_near_vowels_are_more_similar_than_distant_vowels() -> None:
    ih = parse_arpabet(["IH1"]).phones[0]
    iy = parse_arpabet(["IY1"]).phones[0]
    aa = parse_arpabet(["AA1"]).phones[0]

    assert phone_similarity(ih, iy) > phone_similarity(ih, aa)


def test_stress_mismatch_has_an_explicit_similarity_cost() -> None:
    stressed = parse_arpabet(["AY1"]).phones[0]
    unstressed = parse_arpabet(["AY0"]).phones[0]

    assert phone_similarity(stressed, unstressed) == pytest.approx(0.82)
    assert phone_similarity(stressed, unstressed) < phone_similarity(stressed, stressed)
