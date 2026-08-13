"""Deterministic English rhyme candidate generation and classification."""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass
from itertools import combinations
from math import exp, log

from secondear_analysis.dictionaries import Pronunciation
from secondear_analysis.domain import (
    RhymeChain,
    RhymeFamily,
    RhymeOccurrence,
    RhymePair,
    RhymePosition,
    RhymeType,
    SectionScheme,
    SourceSpan,
)
from secondear_analysis.morphology import ConservativeEnglishMorphology
from secondear_analysis.phonetics import (
    Phone,
    phone_similarity,
    rhyme_zone,
    sequence_similarity,
)
from secondear_analysis.text import LyricsDocument, Token

SCORING_TYPES = frozenset({RhymeType.EXACT, RhymeType.NEAR, RhymeType.IDENTITY})


@dataclass(frozen=True, slots=True)
class _ResolvedToken:
    token: Token
    pronunciation: Pronunciation


@dataclass(frozen=True, slots=True)
class _Occurrence:
    public: RhymeOccurrence
    phones: tuple[Phone, ...]
    zone: tuple[Phone, ...]
    onset: Phone | None
    zone_token_count: int


@dataclass(frozen=True, slots=True)
class DetectionResult:
    occurrences: tuple[RhymeOccurrence, ...]
    pairs: tuple[RhymePair, ...]
    families: tuple[RhymeFamily, ...]
    chains: tuple[RhymeChain, ...]
    schemes: tuple[SectionScheme, ...]
    accepted_pair_count: int
    identity_pair_count: int
    same_word_pair_count: int
    same_lemma_pair_count: int
    lemma_comparable_pair_count: int
    internal_pair_count: int
    multisyllabic_pair_count: int
    multiword_pair_count: int
    participating_token_ids: frozenset[str]
    effective_family_diversity: float
    longest_chain: int
    scheme_coverage: float


def _make_occurrence(tokens: tuple[_ResolvedToken, ...], serial: int) -> _Occurrence | None:
    phrase_phones = tuple(
        phone for resolved in tokens for phone in resolved.pronunciation.phones
    )
    phrase_syllables = sum(phone.is_vowel for phone in phrase_phones)
    if phrase_syllables == 0 or phrase_syllables > 4:
        return None
    zone = rhyme_zone(phrase_phones)
    if not zone:
        return None
    zone_start_in_phrase = len(phrase_phones) - len(zone)
    phone_cursor = 0
    first_zone_token = 0
    for token_index, resolved in enumerate(tokens):
        next_cursor = phone_cursor + len(resolved.pronunciation.phones)
        if zone_start_in_phrase < next_cursor:
            first_zone_token = token_index
            break
        phone_cursor = next_cursor
    selected_tokens = tokens[first_zone_token:]
    phones = tuple(
        phone for resolved in selected_tokens for phone in resolved.pronunciation.phones
    )
    zone_start = zone_start_in_phrase - phone_cursor
    onset = phones[zone_start - 1] if zone_start > 0 else None
    syllables = sum(phone.is_vowel for phone in phones)
    first = selected_tokens[0].token
    last = selected_tokens[-1].token
    occurrence_id = f"o{serial}:{first.id}:{last.id}"
    public = RhymeOccurrence(
        id=occurrence_id,
        text=" ".join(resolved.token.text for resolved in selected_tokens),
        normalized_tokens=tuple(resolved.token.normalized for resolved in selected_tokens),
        token_ids=tuple(resolved.token.id for resolved in selected_tokens),
        phonemes=tuple(phone.display for phone in phones),
        rhyme_zone=tuple(phone.display for phone in zone),
        syllable_count=syllables,
        section_index=first.section_index,
        line_index=first.line_index,
        span=SourceSpan(first.line_index, first.span.start, last.span.end),
        is_line_ending=last.is_line_ending,
    )
    return _Occurrence(
        public=public,
        phones=phones,
        zone=zone,
        onset=onset,
        zone_token_count=len(selected_tokens),
    )


def _consonant_similarity(left: tuple[Phone, ...], right: tuple[Phone, ...]) -> float:
    left_consonants = tuple(phone for phone in left if not phone.is_vowel)
    right_consonants = tuple(phone for phone in right if not phone.is_vowel)
    if not left_consonants or not right_consonants:
        return 0.0
    return sequence_similarity(left_consonants, right_consonants)


def _classify(left: _Occurrence, right: _Occurrence) -> tuple[RhymeType, float, float] | None:
    similarity = sequence_similarity(left.zone, right.zone)
    nucleus_similarity = phone_similarity(left.zone[0], right.zone[0])
    same_full_pronunciation = left.phones == right.phones
    same_zone = left.zone == right.zone
    same_onset = (
        left.onset is not None
        and right.onset is not None
        and left.onset.symbol == right.onset.symbol
    )
    if same_full_pronunciation:
        return RhymeType.IDENTITY, similarity, nucleus_similarity
    if same_zone and not same_onset:
        return RhymeType.EXACT, similarity, nucleus_similarity
    if similarity >= 0.72 and nucleus_similarity >= 0.60:
        return RhymeType.NEAR, similarity, nucleus_similarity
    if nucleus_similarity >= 0.80:
        return RhymeType.ASSONANCE, similarity, nucleus_similarity
    consonant_similarity = _consonant_similarity(left.zone, right.zone)
    if consonant_similarity >= 0.75:
        return RhymeType.CONSONANCE, similarity, nucleus_similarity
    return None


def _pair(
    serial: int,
    left: _Occurrence,
    right: _Occurrence,
    position: RhymePosition,
    morphology: ConservativeEnglishMorphology,
) -> RhymePair | None:
    classification = _classify(left, right)
    if classification is None:
        return None
    rhyme_type, similarity, nucleus_similarity = classification
    same_phrase = left.public.normalized_tokens == right.public.normalized_tokens
    same_word = left.public.normalized_tokens[-1] == right.public.normalized_tokens[-1]
    left_lemma = morphology.lemma(left.public.normalized_tokens[-1])
    right_lemma = morphology.lemma(right.public.normalized_tokens[-1])
    lemma_comparable = left_lemma is not None and right_lemma is not None
    same_lemma = (
        not same_word
        and lemma_comparable
        and left_lemma == right_lemma
    )
    homophone = left.phones == right.phones and not same_phrase
    return RhymePair(
        id=f"rp{serial}",
        left_occurrence_id=left.public.id,
        right_occurrence_id=right.public.id,
        rhyme_type=rhyme_type,
        position=position,
        similarity=round(similarity, 4),
        nucleus_similarity=round(nucleus_similarity, 4),
        multisyllabic=min(
            sum(phone.is_vowel for phone in left.zone),
            sum(phone.is_vowel for phone in right.zone),
        )
        >= 2,
        multiword=left.zone_token_count > 1 or right.zone_token_count > 1,
        same_word=same_word,
        lemma_comparable=lemma_comparable,
        same_lemma=same_lemma,
        homophone=homophone,
    )


def _pair_rank(pair: RhymePair, left: _Occurrence, right: _Occurrence) -> tuple[float, ...]:
    type_rank = {
        RhymeType.EXACT: 5.0,
        RhymeType.NEAR: 4.0,
        RhymeType.IDENTITY: 3.0,
        RhymeType.ASSONANCE: 2.0,
        RhymeType.CONSONANCE: 1.0,
    }[pair.rhyme_type]
    return (
        type_rank,
        pair.similarity,
        float(min(left.public.syllable_count, right.public.syllable_count)),
        float(len(left.public.token_ids) + len(right.public.token_ids)),
    )


def _label(index: int) -> str:
    value = index
    result = ""
    while True:
        result = chr(ord("A") + value % 26) + result
        value = value // 26 - 1
        if value < 0:
            return result


def _build_families(
    document: LyricsDocument,
    terminal_pairs: list[RhymePair],
    occurrence_by_id: dict[str, _Occurrence],
) -> tuple[tuple[RhymeFamily, ...], tuple[SectionScheme, ...], int, float]:
    pair_by_lines: dict[tuple[int, int], RhymePair] = {}
    occurrence_ids_by_line: dict[int, set[str]] = {}
    for pair in terminal_pairs:
        if pair.rhyme_type not in SCORING_TYPES:
            continue
        left = occurrence_by_id[pair.left_occurrence_id].public
        right = occurrence_by_id[pair.right_occurrence_id].public
        key = tuple(sorted((left.line_index, right.line_index)))
        previous = pair_by_lines.get(key)
        if previous is None or pair.similarity > previous.similarity:
            pair_by_lines[key] = pair
        occurrence_ids_by_line.setdefault(left.line_index, set()).add(left.id)
        occurrence_ids_by_line.setdefault(right.line_index, set()).add(right.id)

    clusters: list[set[int]] = [{line} for line in sorted(occurrence_ids_by_line)]
    while True:
        candidate: tuple[float, int, int] | None = None
        for left_index, right_index in combinations(range(len(clusters)), 2):
            cross_pairs = [
                pair_by_lines.get(tuple(sorted((left, right))))
                for left in clusters[left_index]
                for right in clusters[right_index]
            ]
            if not cross_pairs or any(pair is None for pair in cross_pairs):
                continue
            minimum = min(pair.similarity for pair in cross_pairs if pair is not None)
            if minimum < 0.72:
                continue
            proposed = (minimum, -left_index, -right_index)
            if candidate is None or proposed > candidate:
                candidate = proposed
        if candidate is None:
            break
        _, negative_left, negative_right = candidate
        left_index = -negative_left
        right_index = -negative_right
        clusters[left_index].update(clusters[right_index])
        del clusters[right_index]

    clusters = [cluster for cluster in clusters if len(cluster) >= 2]
    clusters.sort(key=lambda cluster: min(cluster))
    line_to_label: dict[int, str] = {}
    families: list[RhymeFamily] = []
    for index, cluster in enumerate(clusters):
        label = _label(index)
        for line in cluster:
            line_to_label[line] = label
        occurrence_ids = tuple(
            sorted(
                {item for line in cluster for item in occurrence_ids_by_line.get(line, set())},
                key=lambda occurrence_id: (
                    occurrence_by_id[occurrence_id].public.line_index,
                    occurrence_by_id[occurrence_id].public.span.start,
                    occurrence_by_id[occurrence_id].public.span.end,
                    occurrence_id,
                ),
            )
        )
        families.append(
            RhymeFamily(
                label=label,
                occurrence_ids=occurrence_ids,
                line_indices=tuple(sorted(cluster)),
            )
        )

    schemes: list[SectionScheme] = []
    non_singleton_lines = 0
    total_lines = 0
    for section in document.sections:
        pattern: list[str] = []
        for line in section.lines:
            total_lines += 1
            value = line_to_label.get(line.line_index, "X")
            if value != "X":
                non_singleton_lines += 1
            pattern.append(value)
        schemes.append(
            SectionScheme(
                section_index=section.index,
                label=section.label,
                occurrence_count=section.occurrence_count,
                pattern=tuple(pattern),
            )
        )
    longest_chain = max((len(family.line_indices) for family in families), default=0)
    coverage = non_singleton_lines / total_lines if total_lines else 0.0
    return tuple(families), tuple(schemes), longest_chain, coverage


def _effective_diversity(families: tuple[RhymeFamily, ...]) -> float:
    sizes = [len(family.line_indices) for family in families]
    total = sum(sizes)
    if total == 0:
        return 0.0
    probabilities = [size / total for size in sizes]
    entropy = -sum(probability * log(probability) for probability in probabilities)
    effective = exp(entropy)
    richness = min(1.0, effective / 4.0)
    evenness = effective / len(families)
    return min(1.0, richness * evenness)


def detect_rhymes(
    document: LyricsDocument,
    pronunciations: dict[str, Pronunciation],
    vocabulary: Collection[str],
) -> DetectionResult:
    """Detect terminal and bounded internal rhyme evidence."""

    occurrence_serial = 0
    morphology = ConservativeEnglishMorphology(vocabulary)
    occurrences_by_line: dict[int, list[_Occurrence]] = {}
    occurrence_by_id: dict[str, _Occurrence] = {}
    section_by_line: dict[int, int] = {}

    for section in document.sections:
        for line in section.lines:
            section_by_line[line.line_index] = section.index
            resolved = [
                _ResolvedToken(token=token, pronunciation=pronunciations[token.id])
                for token in line.tokens
                if token.id in pronunciations
            ]
            # Do not bridge over an unresolved word when forming a phrase.
            token_position = {token.id: index for index, token in enumerate(line.tokens)}
            line_occurrences: list[_Occurrence] = []
            seen_occurrence_tokens: set[tuple[str, ...]] = set()
            for end in range(len(resolved)):
                for length in range(1, 4):
                    start = end - length + 1
                    if start < 0:
                        continue
                    selected = tuple(resolved[start : end + 1])
                    positions = [token_position[item.token.id] for item in selected]
                    if positions != list(range(positions[0], positions[0] + len(positions))):
                        continue
                    occurrence = _make_occurrence(selected, occurrence_serial)
                    occurrence_serial += 1
                    if occurrence is None:
                        continue
                    if occurrence.public.token_ids in seen_occurrence_tokens:
                        continue
                    seen_occurrence_tokens.add(occurrence.public.token_ids)
                    line_occurrences.append(occurrence)
                    occurrence_by_id[occurrence.public.id] = occurrence
            occurrences_by_line[line.line_index] = line_occurrences

    terminal_candidates: list[tuple[tuple[float, ...], RhymePair]] = []
    pair_serial = 0
    for section in document.sections:
        lines = list(section.lines)
        for left_offset, left_line in enumerate(lines):
            for right_line in lines[left_offset + 1 : left_offset + 4]:
                left_candidates = [
                    occurrence
                    for occurrence in occurrences_by_line.get(left_line.line_index, [])
                    if occurrence.public.is_line_ending
                ]
                right_candidates = [
                    occurrence
                    for occurrence in occurrences_by_line.get(right_line.line_index, [])
                    if occurrence.public.is_line_ending
                ]
                best: tuple[tuple[float, ...], RhymePair] | None = None
                for left in left_candidates:
                    for right in right_candidates:
                        candidate = _pair(
                            pair_serial,
                            left,
                            right,
                            RhymePosition.LINE_END,
                            morphology,
                        )
                        pair_serial += 1
                        if candidate is None:
                            continue
                        ranked = (_pair_rank(candidate, left, right), candidate)
                        if best is None or ranked[0] > best[0]:
                            best = ranked
                if best is not None:
                    terminal_candidates.append(best)

    terminal_pairs: list[RhymePair] = []
    used_terminal_tokens: set[str] = set()
    for _, pair in sorted(terminal_candidates, key=lambda value: value[0], reverse=True):
        left_tokens = set(occurrence_by_id[pair.left_occurrence_id].public.token_ids)
        right_tokens = set(occurrence_by_id[pair.right_occurrence_id].public.token_ids)
        if (left_tokens | right_tokens) & used_terminal_tokens:
            continue
        terminal_pairs.append(pair)
        used_terminal_tokens.update(left_tokens | right_tokens)

    internal_candidates: list[tuple[tuple[float, ...], RhymePair]] = []
    all_lines = sorted(occurrences_by_line)
    for left_line in all_lines:
        for right_line in range(left_line, left_line + 3):
            if section_by_line.get(left_line) != section_by_line.get(right_line):
                continue
            left_occurrences = occurrences_by_line.get(left_line, [])
            right_occurrences = occurrences_by_line.get(right_line, [])
            for left_position, left in enumerate(left_occurrences):
                for right_position, right in enumerate(right_occurrences):
                    if left_line == right_line and right_position <= left_position:
                        continue
                    if left.public.is_line_ending and right.public.is_line_ending:
                        continue
                    if set(left.public.token_ids) & set(right.public.token_ids):
                        continue
                    candidate = _pair(
                        pair_serial,
                        left,
                        right,
                        RhymePosition.INTERNAL,
                        morphology,
                    )
                    pair_serial += 1
                    if candidate is None:
                        continue
                    internal_candidates.append((_pair_rank(candidate, left, right), candidate))

    internal_pairs: list[RhymePair] = []
    used_internal_tokens: set[str] = set()
    for _, pair in sorted(internal_candidates, key=lambda value: value[0], reverse=True):
        left_tokens = set(occurrence_by_id[pair.left_occurrence_id].public.token_ids)
        right_tokens = set(occurrence_by_id[pair.right_occurrence_id].public.token_ids)
        if (left_tokens | right_tokens) & used_internal_tokens:
            continue
        internal_pairs.append(pair)
        used_internal_tokens.update(left_tokens | right_tokens)

    pairs = terminal_pairs + internal_pairs
    used_occurrence_ids = {
        occurrence_id
        for pair in pairs
        for occurrence_id in (pair.left_occurrence_id, pair.right_occurrence_id)
    }
    used_occurrence_ids.update(
        occurrence_id
        for _, pair in terminal_candidates
        if pair.rhyme_type in SCORING_TYPES
        for occurrence_id in (pair.left_occurrence_id, pair.right_occurrence_id)
    )
    public_occurrences = tuple(
        occurrence_by_id[occurrence_id].public
        for occurrence_id in sorted(
            used_occurrence_ids,
            key=lambda occurrence_id: (
                occurrence_by_id[occurrence_id].public.line_index,
                occurrence_by_id[occurrence_id].public.span.start,
                occurrence_by_id[occurrence_id].public.span.end,
                occurrence_id,
            ),
        )
    )
    families, schemes, longest_chain, scheme_coverage = _build_families(
        document,
        [pair for _, pair in terminal_candidates],
        occurrence_by_id,
    )
    chains = tuple(
        RhymeChain(
            id=f"chain-{family.label}",
            family_label=family.label,
            occurrence_ids=family.occurrence_ids,
            line_indices=family.line_indices,
        )
        for family in families
    )
    accepted = [pair for pair in pairs if pair.rhyme_type in SCORING_TYPES]
    participating = frozenset(
        token_id
        for pair in accepted
        for occurrence_id in (pair.left_occurrence_id, pair.right_occurrence_id)
        for token_id in occurrence_by_id[occurrence_id].public.token_ids
    )
    return DetectionResult(
        occurrences=public_occurrences,
        pairs=tuple(pairs),
        families=families,
        chains=chains,
        schemes=schemes,
        accepted_pair_count=len(accepted),
        identity_pair_count=sum(pair.rhyme_type is RhymeType.IDENTITY for pair in accepted),
        same_word_pair_count=sum(pair.same_word for pair in accepted),
        same_lemma_pair_count=sum(pair.same_lemma for pair in accepted),
        lemma_comparable_pair_count=sum(pair.lemma_comparable for pair in accepted),
        internal_pair_count=sum(pair.position is RhymePosition.INTERNAL for pair in accepted),
        multisyllabic_pair_count=sum(pair.multisyllabic for pair in accepted),
        multiword_pair_count=sum(pair.multiword for pair in accepted),
        participating_token_ids=participating,
        effective_family_diversity=_effective_diversity(families),
        longest_chain=longest_chain,
        scheme_coverage=scheme_coverage,
    )
