"""Versioned pronunciation lexicons for supported English profiles."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from secondear_analysis.domain import LanguageProfile
from secondear_analysis.phonetics import CONSONANTS, VOWELS, Phone

RESOURCE_DIRECTORY = Path(__file__).with_name("resources")
CMUDICT_FILE = RESOURCE_DIRECTORY / "cmudict-0.7b-2026-08-14.dict"
BRITFONE_FILE = RESOURCE_DIRECTORY / "britfone.main.3.0.1.csv"

CMUDICT_VERSION = "0.7b-pinned-2026-08-14"
BRITFONE_VERSION = "3.0.1"

_VARIANT = re.compile(r"\(\d+\)$")
_STRESS = re.compile(r"^(?P<base>[A-Z]+)(?P<stress>[012])?$")

ARPA_TO_CANONICAL: dict[str, str] = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ",
    "AY": "aɪ", "EH": "ɛ", "ER": "ɜr", "EY": "eɪ", "IH": "ɪ",
    "IY": "i", "OW": "oʊ", "OY": "ɔɪ", "UH": "ʊ", "UW": "u",
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "F": "f",
    "G": "g", "HH": "h", "JH": "dʒ", "K": "k", "L": "l",
    "M": "m", "N": "n", "NG": "ŋ", "P": "p", "R": "r",
    "S": "s", "SH": "ʃ", "T": "t", "TH": "θ", "V": "v",
    "W": "w", "Y": "j", "Z": "z", "ZH": "ʒ",
}


@dataclass(frozen=True, slots=True)
class Pronunciation:
    """Canonical phones plus the source notation shown to callers."""

    phones: tuple[Phone, ...]
    notation: str


@dataclass(frozen=True, slots=True)
class PronunciationLexicon:
    """Immutable word-to-pronunciation mapping and provenance."""

    profile: LanguageProfile
    name: str
    version: str
    sha256: str
    entries: dict[str, tuple[Pronunciation, ...]]

    def lookup(self, word: str) -> tuple[Pronunciation, ...]:
        return self.entries.get(word.casefold(), ())

    def parse_override(self, value: str) -> Pronunciation:
        if self.profile is LanguageProfile.EN_US:
            return parse_arpabet(value.split())
        return parse_ipa(value.split())


def _phone(symbol: str, stress: int = 0) -> Phone:
    return Phone(symbol=symbol, is_vowel=symbol in VOWELS, stress=stress)


def parse_arpabet(parts: list[str]) -> Pronunciation:
    """Parse a CMU ARPAbet pronunciation into canonical phones."""

    phones: list[Phone] = []
    for part in parts:
        match = _STRESS.match(part.upper())
        if match is None:
            raise ValueError(f"Unsupported ARPAbet symbol: {part}")
        base = match.group("base")
        canonical = ARPA_TO_CANONICAL.get(base)
        if canonical is None:
            raise ValueError(f"Unsupported ARPAbet symbol: {part}")
        stress = int(match.group("stress") or 0)
        if base == "AH" and stress == 0:
            canonical = "ə"
        elif base == "ER" and stress == 0:
            canonical = "ər"
        phones.append(_phone(canonical, stress))
    if not phones:
        raise ValueError("A pronunciation must contain at least one phone")
    if not any(phone.is_vowel for phone in phones):
        raise ValueError("A pronunciation must contain at least one vowel")
    return Pronunciation(phones=tuple(phones), notation=" ".join(parts).upper())


def parse_ipa(parts: list[str]) -> Pronunciation:
    """Parse Britfone-style space-separated IPA with attached stress marks."""

    phones: list[Phone] = []
    normalized_parts: list[str] = []
    for raw in parts:
        stress = 0
        value = raw.strip()
        if value.startswith("ˈ"):
            stress = 1
            value = value[1:]
        elif value.startswith("ˌ"):
            stress = 2
            value = value[1:]
        value = value.replace("ɡ", "g")
        if value not in VOWELS and value not in CONSONANTS:
            # Unknown IPA remains usable for exact matching. It is a consonant
            # unless it contains a known vowel glyph.
            vowel_glyphs = "aeiouyɑæɐʌəɜɪʊɔɒɛ"
            is_vowel = any(glyph in value for glyph in vowel_glyphs)
            phones.append(Phone(value, is_vowel, stress))
        else:
            phones.append(_phone(value, stress))
        normalized_parts.append(f"{'ˈ' if stress == 1 else 'ˌ' if stress == 2 else ''}{value}")
    if not phones:
        raise ValueError("A pronunciation must contain at least one phone")
    if not any(phone.is_vowel for phone in phones):
        raise ValueError("A pronunciation must contain at least one vowel")
    return Pronunciation(phones=tuple(phones), notation=" ".join(normalized_parts))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_cmudict(path: Path = CMUDICT_FILE) -> PronunciationLexicon:
    """Load the pinned official CMUdict source file without a wrapper package."""

    entries: dict[str, list[Pronunciation]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(";;;"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            continue
        word = _VARIANT.sub("", parts[0]).casefold()
        try:
            pronunciation = parse_arpabet(parts[1:])
        except ValueError:
            continue
        if pronunciation not in entries.setdefault(word, []):
            entries[word].append(pronunciation)
    return PronunciationLexicon(
        profile=LanguageProfile.EN_US,
        name="CMU Pronouncing Dictionary",
        version=CMUDICT_VERSION,
        sha256=_sha256(path),
        entries={word: tuple(values) for word, values in entries.items()},
    )


def load_britfone(path: Path = BRITFONE_FILE) -> PronunciationLexicon:
    """Load the pinned Britfone CSV source file."""

    entries: dict[str, list[Pronunciation]] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or "," not in line:
            continue
        raw_word, raw_pronunciation = line.split(",", 1)
        word = _VARIANT.sub("", raw_word.strip()).replace("_", " ").casefold()
        try:
            pronunciation = parse_ipa(raw_pronunciation.strip().split())
        except ValueError:
            continue
        if pronunciation not in entries.setdefault(word, []):
            entries[word].append(pronunciation)
    return PronunciationLexicon(
        profile=LanguageProfile.EN_GB,
        name="Britfone",
        version=BRITFONE_VERSION,
        sha256=_sha256(path),
        entries={word: tuple(values) for word, values in entries.items()},
    )


@lru_cache(maxsize=2)
def load_default_lexicon(profile: LanguageProfile) -> PronunciationLexicon:
    """Load and cache the configured offline lexicon for a profile."""

    if profile is LanguageProfile.EN_US:
        return load_cmudict()
    return load_britfone()
