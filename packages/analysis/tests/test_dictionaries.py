from __future__ import annotations

from secondear_analysis.dictionaries import (
    load_default_lexicon,
    parse_arpabet,
    parse_ipa,
)
from secondear_analysis.domain import LanguageProfile


def test_pinned_lexicons_have_expected_identity_and_coverage() -> None:
    us = load_default_lexicon(LanguageProfile.EN_US)
    gb = load_default_lexicon(LanguageProfile.EN_GB)

    assert us.sha256 == "81917843c7f44ce2b094ac63873c2c7a4cf802040792c455ba3ca406891c3d22"
    assert gb.sha256 == "59f197e98520856d1cc88e380beb54e4314d8712efc4d588b6778819c502d920"
    assert len(us.entries) > 120_000
    assert len(gb.entries) > 15_000


def test_profile_specific_car_pronunciation_is_not_mixed() -> None:
    us = load_default_lexicon(LanguageProfile.EN_US).lookup("car")[0]
    gb = load_default_lexicon(LanguageProfile.EN_GB).lookup("car")[0]

    assert us.notation == "K AA1 R"
    assert gb.notation == "k ˈɑː"
    assert us.phones != gb.phones


def test_en_gb_does_not_fall_back_to_an_en_us_entry() -> None:
    us = load_default_lexicon(LanguageProfile.EN_US)
    gb = load_default_lexicon(LanguageProfile.EN_GB)
    us_only = next(
        word for word in sorted(us.entries) if word.isalpha() and word not in gb.entries
    )

    assert us.lookup(us_only)
    assert gb.lookup(us_only) == ()


def test_override_parsers_require_a_vowel() -> None:
    assert parse_arpabet(["N", "AY1", "T"]).notation == "N AY1 T"
    assert parse_ipa(["n", "ˈaɪ", "t"]).notation == "n ˈaɪ t"


def test_homograph_and_contraction_variants_remain_visible() -> None:
    us = load_default_lexicon(LanguageProfile.EN_US)

    assert len(us.lookup("read")) >= 2
    assert us.lookup("we're")
