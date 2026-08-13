"""Profile-neutral phoneme representation and weighted similarity."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

FEATURES_VERSION = "english-phone-features-0.1.0"


@dataclass(frozen=True, slots=True)
class Phone:
    symbol: str
    is_vowel: bool
    stress: int

    @property
    def display(self) -> str:
        marker = "ˈ" if self.stress == 1 else "ˌ" if self.stress == 2 else ""
        return f"{marker}{self.symbol}"


# height, backness, rounded, diphthong trajectory. Values are intentionally
# inspectable approximations, not acoustic measurements.
VOWELS: dict[str, tuple[float, float, float, float]] = {
    "i": (0.0, 0.0, 0.0, 0.0),
    "iː": (0.0, 0.0, 0.0, 0.0),
    "ɪ": (0.2, 0.1, 0.0, 0.0),
    "e": (0.35, 0.0, 0.0, 0.0),
    "eɪ": (0.25, 0.0, 0.0, 0.7),
    "ɛ": (0.5, 0.0, 0.0, 0.0),
    "æ": (0.75, 0.0, 0.0, 0.0),
    "a": (1.0, 0.35, 0.0, 0.0),
    "ɑ": (1.0, 1.0, 0.0, 0.0),
    "ɑː": (1.0, 1.0, 0.0, 0.0),
    "ɒ": (0.8, 1.0, 0.8, 0.0),
    "ɐ": (0.75, 0.5, 0.0, 0.0),
    "ʌ": (0.65, 0.65, 0.0, 0.0),
    "ə": (0.5, 0.5, 0.0, 0.0),
    "ɜ": (0.5, 0.5, 0.0, 0.0),
    "ɜː": (0.5, 0.5, 0.0, 0.0),
    "ɜr": (0.5, 0.5, 0.0, 0.1),
    "ər": (0.5, 0.5, 0.0, 0.1),
    "u": (0.0, 1.0, 1.0, 0.0),
    "uː": (0.0, 1.0, 1.0, 0.0),
    "ʊ": (0.2, 0.9, 1.0, 0.0),
    "o": (0.35, 1.0, 1.0, 0.0),
    "oʊ": (0.3, 1.0, 1.0, 0.6),
    "əʊ": (0.4, 0.8, 1.0, 0.6),
    "ɔ": (0.55, 1.0, 1.0, 0.0),
    "ɔː": (0.55, 1.0, 1.0, 0.0),
    "aɪ": (0.8, 0.25, 0.0, 1.0),
    "aʊ": (0.8, 0.65, 0.5, 1.0),
    "ɔɪ": (0.55, 0.65, 0.7, 1.0),
    "ɛɪ": (0.4, 0.1, 0.0, 0.7),
    "ɐʊ": (0.75, 0.65, 0.5, 1.0),
    "ɪə": (0.25, 0.25, 0.0, 0.8),
    "eə": (0.5, 0.25, 0.0, 0.8),
    "ʊə": (0.3, 0.75, 1.0, 0.8),
}

# place, manner, voice. Place is ordered only to make adjacent articulations
# less costly than distant ones.
CONSONANTS: dict[str, tuple[float, str, float]] = {
    "p": (0.0, "stop", 0.0), "b": (0.0, "stop", 1.0),
    "m": (0.0, "nasal", 1.0), "f": (0.15, "fricative", 0.0),
    "v": (0.15, "fricative", 1.0), "θ": (0.3, "fricative", 0.0),
    "ð": (0.3, "fricative", 1.0), "t": (0.4, "stop", 0.0),
    "d": (0.4, "stop", 1.0), "n": (0.4, "nasal", 1.0),
    "s": (0.4, "fricative", 0.0), "z": (0.4, "fricative", 1.0),
    "l": (0.4, "lateral", 1.0), "r": (0.45, "approximant", 1.0),
    "ɹ": (0.45, "approximant", 1.0), "ʃ": (0.55, "fricative", 0.0),
    "ʒ": (0.55, "fricative", 1.0), "tʃ": (0.55, "affricate", 0.0),
    "dʒ": (0.55, "affricate", 1.0), "j": (0.65, "approximant", 1.0),
    "k": (0.8, "stop", 0.0), "g": (0.8, "stop", 1.0),
    "ŋ": (0.8, "nasal", 1.0), "w": (0.9, "approximant", 1.0),
    "h": (1.0, "fricative", 0.0), "x": (0.9, "fricative", 0.0),
    "ʔ": (1.0, "stop", 0.0),
}


def phone_similarity(left: Phone, right: Phone) -> float:
    """Return a symmetric articulatory-feature similarity in ``[0, 1]``."""

    stress_similarity = 1.0
    if left.is_vowel and right.is_vowel and left.stress != right.stress:
        stress_similarity = {
            frozenset({0, 1}): 0.82,
            frozenset({0, 2}): 0.90,
            frozenset({1, 2}): 0.95,
        }.get(frozenset({left.stress, right.stress}), 0.82)
    if left.symbol == right.symbol:
        return stress_similarity
    if left.is_vowel != right.is_vowel:
        return 0.0
    if left.is_vowel:
        a = VOWELS.get(left.symbol)
        b = VOWELS.get(right.symbol)
        if a is None or b is None:
            return 0.0
        distance = (
            0.35 * abs(a[0] - b[0])
            + 0.30 * abs(a[1] - b[1])
            + 0.15 * abs(a[2] - b[2])
            + 0.20 * abs(a[3] - b[3])
        )
        return max(0.0, 1.0 - distance) * stress_similarity
    a_consonant = CONSONANTS.get(left.symbol)
    b_consonant = CONSONANTS.get(right.symbol)
    if a_consonant is None or b_consonant is None:
        return 0.0
    place = max(0.0, 1.0 - abs(a_consonant[0] - b_consonant[0]))
    manner = 1.0 if a_consonant[1] == b_consonant[1] else 0.0
    voice = 1.0 if a_consonant[2] == b_consonant[2] else 0.0
    return 0.4 * place + 0.4 * manner + 0.2 * voice


def _importance(phone: Phone) -> float:
    if not phone.is_vowel:
        return 1.0
    if phone.stress == 1:
        return 2.0
    if phone.stress == 2:
        return 1.6
    return 1.2


def sequence_similarity(left: tuple[Phone, ...], right: tuple[Phone, ...]) -> float:
    """Feature-weighted Levenshtein similarity with symmetric costs."""

    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    previous = [0.0]
    for phone in right:
        previous.append(previous[-1] + _importance(phone))
    for left_phone in left:
        current = [previous[0] + _importance(left_phone)]
        for column, right_phone in enumerate(right, start=1):
            weight = (_importance(left_phone) + _importance(right_phone)) / 2.0
            substitution = previous[column - 1] + weight * (
                1.0 - phone_similarity(left_phone, right_phone)
            )
            deletion = previous[column] + _importance(left_phone)
            insertion = current[column - 1] + _importance(right_phone)
            current.append(min(substitution, deletion, insertion))
        previous = current
    denominator = max(
        sum(_importance(phone) for phone in left),
        sum(_importance(phone) for phone in right),
    )
    result = max(0.0, min(1.0, 1.0 - previous[-1] / denominator))
    return result if isfinite(result) else 0.0


def last_stressed_vowel(phones: tuple[Phone, ...]) -> int | None:
    """Locate the final lexically stressed vowel, then fall back to any vowel."""

    for index in range(len(phones) - 1, -1, -1):
        if phones[index].is_vowel and phones[index].stress > 0:
            return index
    for index in range(len(phones) - 1, -1, -1):
        if phones[index].is_vowel:
            return index
    return None


def rhyme_zone(phones: tuple[Phone, ...]) -> tuple[Phone, ...]:
    index = last_stressed_vowel(phones)
    return phones[index:] if index is not None else ()
