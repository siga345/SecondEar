"""Conservative English morphology for lexical-diversity evidence.

The adapter only returns a derived lemma when a single dictionary-backed
candidate exists. Unknown or ambiguous transformations return ``None`` and
therefore do not reduce the Rhymes score.
"""

from __future__ import annotations

from collections.abc import Collection

MORPHOLOGY_VERSION = "english-conservative-morphology-0.1.0"

_IRREGULAR_FORMS = {
    "better": "good",
    "best": "good",
    "brought": "bring",
    "came": "come",
    "children": "child",
    "did": "do",
    "done": "do",
    "feet": "foot",
    "found": "find",
    "gave": "give",
    "given": "give",
    "gone": "go",
    "kept": "keep",
    "knew": "know",
    "known": "know",
    "left": "leave",
    "men": "man",
    "mice": "mouse",
    "ran": "run",
    "sang": "sing",
    "sung": "sing",
    "taught": "teach",
    "teeth": "tooth",
    "thought": "think",
    "took": "take",
    "taken": "take",
    "went": "go",
    "women": "woman",
    "worse": "bad",
    "worst": "bad",
    "wrote": "write",
    "written": "write",
}


def _suffix_candidates(word: str) -> set[str]:
    candidates: set[str] = set()
    if len(word) > 4 and word.endswith("ies"):
        candidates.add(word[:-3] + "y")
    if len(word) > 4 and word.endswith("ied"):
        candidates.add(word[:-3] + "y")
    if len(word) > 5 and word.endswith("ing"):
        stem = word[:-3]
        candidates.update({stem, stem + "e"})
        if len(stem) >= 2 and stem[-1] == stem[-2]:
            candidates.add(stem[:-1])
    if len(word) > 4 and word.endswith("ed"):
        stem = word[:-2]
        candidates.update({stem, stem + "e"})
        if len(stem) >= 2 and stem[-1] == stem[-2]:
            candidates.add(stem[:-1])
    if len(word) > 4 and word.endswith("es"):
        candidates.update({word[:-1], word[:-2]})
    if (
        len(word) > 3
        and word.endswith("s")
        and not word.endswith(("ss", "us", "is"))
    ):
        candidates.add(word[:-1])
    return candidates


class ConservativeEnglishMorphology:
    """Return only unambiguous lemmas supported by the active lexicon."""

    def __init__(self, vocabulary: Collection[str]) -> None:
        self._vocabulary = vocabulary

    def lemma(self, word: str) -> str | None:
        """Return a lemma or ``None`` when the result is not defensible."""

        normalized = word.casefold()
        irregular = _IRREGULAR_FORMS.get(normalized)
        if irregular is not None:
            return irregular if irregular in self._vocabulary else None
        candidates = {
            candidate
            for candidate in _suffix_candidates(normalized)
            if candidate in self._vocabulary
        }
        if len(candidates) == 1:
            return candidates.pop()
        if not candidates and normalized in self._vocabulary:
            return normalized
        return None

    def phrase_lemma(self, words: tuple[str, ...]) -> tuple[str, ...] | None:
        """Return a phrase lemma only when every word resolves uniquely."""

        lemmas = tuple(self.lemma(word) for word in words)
        if any(lemma is None for lemma in lemmas):
            return None
        return tuple(lemma for lemma in lemmas if lemma is not None)
