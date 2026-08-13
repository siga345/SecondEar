"""Published seed formula for the English Rhymes criterion."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from math import log

from secondear_analysis.domain import Metric, PrimaryTag
from secondear_analysis.rhyme import SCORING_TYPES, DetectionResult

FORMULA_VERSION = "english-rhymes-score-0.1.0"
PROFILE_VERSION = "english-rhymes-seed-profiles-0.1.0"

COMPONENT_KEYS = (
    "phonetic_strength",
    "rhyme_density_and_coverage",
    "construction_complexity",
    "family_and_lexical_diversity",
    "scheme_and_section_development",
)

WEIGHTS: dict[PrimaryTag, tuple[float, float, float, float, float]] = {
    PrimaryTag.RAP: (0.20, 0.25, 0.25, 0.20, 0.10),
    PrimaryTag.POP: (0.25, 0.20, 0.15, 0.15, 0.25),
    PrimaryTag.RNB: (0.25, 0.20, 0.20, 0.15, 0.20),
    PrimaryTag.ROCK: (0.30, 0.15, 0.15, 0.20, 0.20),
    PrimaryTag.COUNTRY: (0.30, 0.15, 0.10, 0.25, 0.20),
    PrimaryTag.ELECTRONIC: (0.25, 0.15, 0.10, 0.15, 0.35),
}

# Seed anchors are public and versioned. Calibration tooling can replace them
# with owner-corpus values without changing detector behavior.
ANCHORS: dict[PrimaryTag, dict[str, tuple[float, float, float]]] = {
    tag: {
        "phonetic_strength": (0.25, 0.60, 0.88),
        "rhyme_density_and_coverage": (0.08, 0.28, 0.58),
        "construction_complexity": (0.03, 0.22, 0.58),
        "family_and_lexical_diversity": (0.20, 0.52, 0.82),
        "scheme_and_section_development": (0.15, 0.50, 0.85),
    }
    for tag in PrimaryTag
}
ANCHORS[PrimaryTag.RAP]["rhyme_density_and_coverage"] = (0.15, 0.40, 0.72)
ANCHORS[PrimaryTag.RAP]["construction_complexity"] = (0.10, 0.42, 0.78)
ANCHORS[PrimaryTag.ELECTRONIC]["rhyme_density_and_coverage"] = (0.04, 0.18, 0.45)
ANCHORS[PrimaryTag.ELECTRONIC]["construction_complexity"] = (0.01, 0.12, 0.38)
ANCHORS[PrimaryTag.COUNTRY]["family_and_lexical_diversity"] = (0.25, 0.58, 0.86)


@dataclass(frozen=True, slots=True)
class ScoreResult:
    score: float
    index: float
    raw_components: dict[str, float]
    subscores: dict[str, float]
    metrics: tuple[Metric, ...]


def _piecewise(value: float, anchors: tuple[float, float, float]) -> float:
    low, midpoint, high = anchors
    points = ((0.0, 0.0), (low, 0.2), (midpoint, 0.5), (high, 0.8), (1.0, 1.0))
    bounded = max(0.0, min(1.0, value))
    for (left_x, left_y), (right_x, right_y) in pairwise(points):
        if bounded <= right_x:
            if right_x == left_x:
                return right_y
            ratio = (bounded - left_x) / (right_x - left_x)
            return left_y + ratio * (right_y - left_y)
    return 1.0


def _lexical_diversity(detection: DetectionResult) -> float:
    accepted = [pair for pair in detection.pairs if pair.rhyme_type in SCORING_TYPES]
    if not accepted:
        return 0.0
    occurrence_by_id = {occurrence.id: occurrence for occurrence in detection.occurrences}
    phrases = [
        occurrence_by_id[occurrence_id].normalized_tokens
        for pair in accepted
        for occurrence_id in (pair.left_occurrence_id, pair.right_occurrence_id)
    ]
    return len(set(phrases)) / len(phrases)


def _family_entropy(detection: DetectionResult) -> float:
    sizes = [len(family.line_indices) for family in detection.families]
    total = sum(sizes)
    if total <= 1 or len(sizes) <= 1:
        return 0.0
    entropy = -sum((size / total) * log(size / total) for size in sizes)
    return entropy / log(len(sizes))


def calculate_score(
    detection: DetectionResult,
    primary_tag: PrimaryTag,
    lexical_tokens: int,
    unique_lines: int,
) -> ScoreResult:
    """Calculate formula 0.1 independently from confidence."""

    accepted = [pair for pair in detection.pairs if pair.rhyme_type in SCORING_TYPES]
    relation_count = max(1, len(accepted))
    strength = sum(pair.similarity for pair in accepted) / relation_count if accepted else 0.0
    density = len(detection.participating_token_ids) / max(1, lexical_tokens)
    complexity = (
        0.4 * detection.internal_pair_count / relation_count
        + 0.4 * detection.multisyllabic_pair_count / relation_count
        + 0.2 * detection.multiword_pair_count / relation_count
    )
    identity_rate = detection.identity_pair_count / relation_count if accepted else 0.0
    same_word_rate = detection.same_word_pair_count / relation_count if accepted else 0.0
    known_lemma_relations = detection.lemma_comparable_pair_count
    same_lemma_rate = (
        detection.same_lemma_pair_count / known_lemma_relations
        if known_lemma_relations
        else 0.0
    )
    morphological_variety = 1.0 - same_lemma_rate if known_lemma_relations else 1.0
    diversity = (
        0.25 * _lexical_diversity(detection)
        + 0.25 * detection.effective_family_diversity
        + 0.20 * (1.0 - identity_rate)
        + 0.15 * (1.0 - same_word_rate)
        + 0.15 * morphological_variety
        if accepted
        else 0.0
    )
    chain_control = min(1.0, detection.longest_chain / 4.0)
    development = 0.7 * detection.scheme_coverage + 0.3 * chain_control
    raw_values = (strength, density, complexity, diversity, development)
    raw_components = {
        key: round(max(0.0, min(1.0, value)), 4)
        for key, value in zip(COMPONENT_KEYS, raw_values, strict=True)
    }
    subscores = {
        key: round(_piecewise(raw_components[key], ANCHORS[primary_tag][key]), 4)
        for key in COMPONENT_KEYS
    }
    index = sum(
        subscores[key] * weight
        for key, weight in zip(COMPONENT_KEYS, WEIGHTS[primary_tag], strict=True)
    )
    score = max(1.0, min(10.0, round(1.0 + 9.0 * index, 1)))
    metrics = tuple(
        Metric(f"raw_component_{key}", value, "ratio", "derived")
        for key, value in raw_components.items()
    ) + (
        Metric("accepted_rhyme_pair_count", len(accepted), "pairs", "derived"),
        Metric("rhyme_participation_rate", round(density, 4), "ratio", "derived"),
        Metric("identity_rhyme_rate", round(identity_rate, 4), "ratio", "derived"),
        Metric("same_word_rhyme_rate", round(same_word_rate, 4), "ratio", "derived"),
        Metric("same_lemma_rhyme_rate", round(same_lemma_rate, 4), "ratio", "derived"),
        Metric(
            "lemma_comparable_pair_count",
            known_lemma_relations,
            "pairs",
            "estimated",
        ),
        Metric(
            "internal_rhyme_rate",
            round(detection.internal_pair_count / relation_count if accepted else 0.0, 4),
            "ratio",
            "derived",
        ),
        Metric(
            "multisyllabic_rhyme_rate",
            round(detection.multisyllabic_pair_count / relation_count if accepted else 0.0, 4),
            "ratio",
            "derived",
        ),
        Metric("rhyme_family_count", len(detection.families), "families", "derived"),
        Metric("family_entropy", round(_family_entropy(detection), 4), "ratio", "derived"),
        Metric("longest_rhyme_chain", detection.longest_chain, "lines", "derived"),
        Metric("rhyme_scheme_coverage", round(detection.scheme_coverage, 4), "ratio", "derived"),
        Metric("unique_line_count", unique_lines, "lines", "measured"),
        Metric("formula_index", round(index, 4), "ratio", "derived"),
    )
    return ScoreResult(
        score=score,
        index=round(index, 4),
        raw_components=raw_components,
        subscores=subscores,
        metrics=metrics,
    )
