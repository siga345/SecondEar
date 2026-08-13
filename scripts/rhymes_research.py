"""Lawful local-corpus analysis and validation for English Rhymes.

This command never writes source lyrics to its output. It records a SHA-256
identity, derived features, detected line-pair labels, and version metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from secondear_analysis import (
    LanguageProfile,
    PrimaryTag,
    RhymeAnalysisRequest,
    analyze_rhymes,
)

SPLITS = frozenset({"calibration", "validation", "holdout"})
ACCEPTED_TYPES = frozenset({"exact", "near", "identity"})


@dataclass(frozen=True, slots=True)
class Thresholds:
    exact_f1: float = 0.95
    accepted_macro_f1: float = 0.85
    spearman: float = 0.70
    owner_mae_pilot: float = 1.25
    owner_mae_full: float = 1.00


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: invalid JSON: {error}") from error
        if not isinstance(value, dict):
            raise TypeError(f"{path}:{line_number}: every record must be an object")
        records.append(value)
    return records


def _write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as destination:
        for record in records:
            destination.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _validate_manifest(records: list[dict[str, Any]]) -> None:
    writer_splits: dict[str, set[str]] = defaultdict(set)
    seen_ids: set[str] = set()
    for record in records:
        required = {
            "id", "lyrics_path", "songwriter_id", "primary_tag", "language_profile", "split"
        }
        missing = required - record.keys()
        if missing:
            raise ValueError(f"Record is missing fields: {', '.join(sorted(missing))}")
        record_id = str(record["id"])
        if record_id in seen_ids:
            raise ValueError(f"Duplicate record id: {record_id}")
        seen_ids.add(record_id)
        split = str(record["split"])
        if split not in SPLITS:
            raise ValueError(f"Unsupported split for {record_id}: {split}")
        PrimaryTag(str(record["primary_tag"]))
        LanguageProfile(str(record["language_profile"]))
        annotations = record.get("annotations", [])
        if not isinstance(annotations, list):
            raise TypeError(f"Annotations for {record_id} must be a list")
        annotator_ids: set[str] = set()
        for annotation in annotations:
            if not isinstance(annotation, dict):
                raise TypeError(f"Every annotation for {record_id} must be an object")
            annotator_id = str(annotation.get("annotator_id", "")).strip()
            if not annotator_id or annotator_id in annotator_ids:
                raise ValueError(f"Invalid or duplicate annotator_id for {record_id}")
            annotator_ids.add(annotator_id)
            score = float(annotation.get("score", math.nan))
            if not math.isfinite(score) or not 1.0 <= score <= 10.0:
                raise ValueError(f"Annotation score for {record_id} must be in [1, 10]")
        writer_splits[str(record["songwriter_id"])].add(split)
    leaked = {writer: splits for writer, splits in writer_splits.items() if len(splits) > 1}
    if leaked:
        details = ", ".join(f"{writer}={sorted(splits)}" for writer, splits in sorted(leaked.items()))
        raise ValueError(f"Songwriter leakage across splits: {details}")


def analyze_manifest(manifest_path: Path, output_path: Path) -> int:
    records = _read_jsonl(manifest_path)
    _validate_manifest(records)
    output: list[dict[str, Any]] = []
    for record in records:
        lyrics_path = Path(str(record["lyrics_path"]))
        if not lyrics_path.is_absolute():
            lyrics_path = Path.cwd() / lyrics_path
        raw = lyrics_path.read_bytes()
        lyrics = raw.decode("utf-8")
        result = analyze_rhymes(
            RhymeAnalysisRequest(
                lyrics=lyrics,
                language_profile=LanguageProfile(str(record["language_profile"])),
                primary_tag=PrimaryTag(str(record["primary_tag"])),
                source_reference=None,
            )
        )
        occurrence_by_id = {occurrence.id: occurrence for occurrence in result.occurrences}
        detected_pairs = sorted(
            {
                (
                    min(
                        occurrence_by_id[pair.left_occurrence_id].line_index,
                        occurrence_by_id[pair.right_occurrence_id].line_index,
                    ),
                    max(
                        occurrence_by_id[pair.left_occurrence_id].line_index,
                        occurrence_by_id[pair.right_occurrence_id].line_index,
                    ),
                    pair.rhyme_type.value,
                    pair.position.value,
                )
                for pair in result.pairs
            }
        )
        annotations = [
            {
                "annotator_id": str(annotation["annotator_id"]),
                "score": float(annotation["score"]),
                "disputed": bool(annotation.get("disputed", False)),
                "dispute_codes": sorted(
                    str(code) for code in annotation.get("dispute_codes", [])
                ),
            }
            for annotation in record.get("annotations", [])
        ]
        annotation_scores = [annotation["score"] for annotation in annotations]
        pairwise_differences = [
            abs(left - right)
            for index, left in enumerate(annotation_scores)
            for right in annotation_scores[index + 1 :]
        ]
        annotation_summary = {
            "count": len(annotations),
            "mean_score": round(mean(annotation_scores), 4) if annotation_scores else None,
            "score_range": (
                round(max(annotation_scores) - min(annotation_scores), 4)
                if annotation_scores
                else None
            ),
            "pairwise_mae": (
                round(mean(pairwise_differences), 4) if pairwise_differences else None
            ),
            "disputed": any(annotation["disputed"] for annotation in annotations),
        }
        output.append(
            {
                "id": record["id"],
                "songwriter_id": record["songwriter_id"],
                "primary_tag": record["primary_tag"],
                "language_profile": record["language_profile"],
                "split": record["split"],
                "owner_score": record.get("owner_score"),
                "annotations": annotations,
                "annotation_summary": annotation_summary,
                "recognition_cohort": record.get("recognition_cohort"),
                "gold_pairs": record.get("gold_pairs", []),
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "status": result.status.value,
                "score": result.score,
                "confidence": result.confidence,
                "subscores": result.subscores,
                "metrics": {metric.key: metric.value for metric in result.metrics},
                "detected_pairs": [
                    {
                        "left_line": left,
                        "right_line": right,
                        "rhyme_type": rhyme_type,
                        "position": position,
                    }
                    for left, right, rhyme_type, position in detected_pairs
                ],
                "versions": asdict(result.versions),
            }
        )
    _write_jsonl(output_path, output)
    return 0


def _rank(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    cursor = 0
    while cursor < len(indexed):
        end = cursor + 1
        while end < len(indexed) and indexed[end][1] == indexed[cursor][1]:
            end += 1
        average_rank = (cursor + 1 + end) / 2.0
        for index in range(cursor, end):
            ranks[indexed[index][0]] = average_rank
        cursor = end
    return ranks


def _pearson(left: list[float], right: list[float]) -> float:
    if len(left) < 2 or len(left) != len(right):
        return math.nan
    left_mean = mean(left)
    right_mean = mean(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=True))
    denominator = math.sqrt(
        sum((value - left_mean) ** 2 for value in left)
        * sum((value - right_mean) ** 2 for value in right)
    )
    return numerator / denominator if denominator else math.nan


def _f1(
    predicted: set[tuple[int, int, str]],
    gold: set[tuple[int, int, str]],
) -> float:
    true_positive = len(predicted & gold)
    false_positive = len(predicted - gold)
    false_negative = len(gold - predicted)
    denominator = 2 * true_positive + false_positive + false_negative
    return 2 * true_positive / denominator if denominator else 1.0


def _pair_set(
    pairs: list[dict[str, Any]],
    accepted_types: set[str] | frozenset[str],
    positions: set[str] | frozenset[str] | None = None,
) -> set[tuple[int, int, str]]:
    return {
        (
            int(pair["left_line"]),
            int(pair["right_line"]),
            str(pair.get("position", "line_end")),
        )
        for pair in pairs
        if str(pair["rhyme_type"]) in accepted_types
        and (positions is None or str(pair.get("position", "line_end")) in positions)
    }


def validate_results(
    results_path: Path,
    split: str = "holdout",
    annotation_stage: str = "multi",
) -> tuple[int, dict[str, Any]]:
    records = [record for record in _read_jsonl(results_path) if record.get("split") == split]
    scored = [
        record for record in records if record.get("score") is not None and record.get("owner_score") is not None
    ]
    scores = [float(record["score"]) for record in scored]
    owner_scores = [float(record["owner_score"]) for record in scored]
    spearman = _pearson(_rank(scores), _rank(owner_scores))
    mae = mean(abs(left - right) for left, right in zip(scores, owner_scores, strict=True)) if scored else math.nan

    exact_values: list[float] = []
    accepted_by_profile: dict[str, list[float]] = defaultdict(list)
    for record in records:
        predicted = list(record.get("detected_pairs", []))
        gold = list(record.get("gold_pairs", []))
        exact_values.append(
            _f1(
                _pair_set(predicted, {"exact"}, {"line_end"}),
                _pair_set(gold, {"exact"}, {"line_end"}),
            )
        )
        accepted_by_profile[str(record["language_profile"])].append(
            _f1(_pair_set(predicted, ACCEPTED_TYPES), _pair_set(gold, ACCEPTED_TYPES))
        )

    exact_f1 = mean(exact_values) if exact_values else math.nan
    accepted_macro_f1 = {
        profile: mean(values) for profile, values in sorted(accepted_by_profile.items())
    }
    thresholds = Thresholds()
    mae_limit = (
        thresholds.owner_mae_pilot
        if annotation_stage == "pilot"
        else thresholds.owner_mae_full
    )
    checks = {
        "exact_f1": math.isfinite(exact_f1) and exact_f1 >= thresholds.exact_f1,
        "accepted_macro_f1_en-US": accepted_macro_f1.get("en-US", math.nan)
        >= thresholds.accepted_macro_f1,
        "accepted_macro_f1_en-GB": accepted_macro_f1.get("en-GB", math.nan)
        >= thresholds.accepted_macro_f1,
        "spearman": math.isfinite(spearman) and spearman >= thresholds.spearman,
        "owner_mae": math.isfinite(mae) and mae <= mae_limit,
    }
    report = {
        "split": split,
        "annotation_stage": annotation_stage,
        "record_count": len(records),
        "scored_record_count": len(scored),
        "exact_f1": round(exact_f1, 4) if math.isfinite(exact_f1) else None,
        "accepted_macro_f1": {
            profile: round(value, 4) for profile, value in accepted_macro_f1.items()
        },
        "spearman": round(spearman, 4) if math.isfinite(spearman) else None,
        "owner_score_mae": round(mae, 4) if math.isfinite(mae) else None,
        "owner_score_mae_limit": mae_limit,
        "annotation_summary": {
            "records_with_three_annotators": sum(
                int(record.get("annotation_summary", {}).get("count", 0)) >= 3
                for record in records
            ),
            "disputed_record_count": sum(
                bool(record.get("annotation_summary", {}).get("disputed", False))
                for record in records
            ),
        },
        "checks": checks,
        "passed": all(checks.values()),
    }
    return (0 if report["passed"] else 1), report


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Cannot calculate a quantile from an empty sample")
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def calibrate_results(results_path: Path, output_path: Path) -> int:
    """Derive transparent 20th/50th/80th component anchors from the owner pilot."""

    records = [
        record
        for record in _read_jsonl(results_path)
        if record.get("split") == "calibration" and record.get("status") == "evaluated"
    ]
    by_tag: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_tag[str(record["primary_tag"])].append(record)
    missing = [tag.value for tag in PrimaryTag if len(by_tag[tag.value]) < 10]
    if missing:
        counts = ", ".join(f"{tag}={len(by_tag[tag])}" for tag in missing)
        raise ValueError(f"Calibration requires at least 10 evaluated texts per tag: {counts}")

    component_keys = (
        "phonetic_strength",
        "rhyme_density_and_coverage",
        "construction_complexity",
        "family_and_lexical_diversity",
        "scheme_and_section_development",
    )
    profiles: dict[str, dict[str, list[float]]] = {}
    for tag in PrimaryTag:
        anchors: dict[str, list[float]] = {}
        for component in component_keys:
            metric_key = f"raw_component_{component}"
            values = [float(record["metrics"][metric_key]) for record in by_tag[tag.value]]
            anchors[component] = [
                round(_quantile(values, probability), 4)
                for probability in (0.20, 0.50, 0.80)
            ]
        profiles[tag.value] = anchors
    formula_versions = sorted(
        {str(record["versions"]["formula_version"]) for record in records}
    )
    if len(formula_versions) != 1:
        raise ValueError("Calibration records must use exactly one formula version")
    payload = {
        "profile_version": "english-rhymes-owner-pilot-0.1.0",
        "formula_version": formula_versions[0],
        "anchor_quantiles": [0.20, 0.50, 0.80],
        "minimum_texts_per_tag": 10,
        "sample_counts": {tag.value: len(by_tag[tag.value]) for tag in PrimaryTag},
        "profiles": profiles,
    }
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a private local manifest")
    analyze_parser.add_argument("manifest", type=Path)
    analyze_parser.add_argument("output", type=Path)
    calibrate_parser = subparsers.add_parser(
        "calibrate", help="Derive owner-pilot component anchors"
    )
    calibrate_parser.add_argument("results", type=Path)
    calibrate_parser.add_argument("output", type=Path)
    validate_parser = subparsers.add_parser("validate", help="Validate derived results")
    validate_parser.add_argument("results", type=Path)
    validate_parser.add_argument("--split", choices=sorted(SPLITS), default="holdout")
    validate_parser.add_argument(
        "--annotation-stage", choices=("pilot", "multi"), default="multi"
    )
    arguments = parser.parse_args(argv)
    if arguments.command == "analyze":
        return analyze_manifest(arguments.manifest, arguments.output)
    if arguments.command == "calibrate":
        return calibrate_results(arguments.results, arguments.output)
    exit_code, report = validate_results(
        arguments.results,
        arguments.split,
        arguments.annotation_stage,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, TypeError, UnicodeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
