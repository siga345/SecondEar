from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.rhymes_research import (
    _validate_manifest,
    analyze_manifest,
    calibrate_results,
    validate_results,
)


def test_manifest_rejects_songwriter_leakage() -> None:
    records = [
        {
            "id": "one",
            "lyrics_path": "one.txt",
            "songwriter_id": "writer",
            "primary_tag": "pop",
            "language_profile": "en-US",
            "split": "calibration",
        },
        {
            "id": "two",
            "lyrics_path": "two.txt",
            "songwriter_id": "writer",
            "primary_tag": "rock",
            "language_profile": "en-US",
            "split": "holdout",
        },
    ]
    with pytest.raises(ValueError, match="Songwriter leakage"):
        _validate_manifest(records)


def test_private_analysis_preserves_scores_not_source_text(tmp_path: Path) -> None:
    lyrics = tmp_path / "private.txt"
    manifest = tmp_path / "manifest.jsonl"
    output = tmp_path / "derived.jsonl"
    lyrics.write_text("A private line ending in light\nAnother line ending at night", encoding="utf-8")
    manifest.write_text(
        json.dumps(
            {
                "id": "private-1",
                "lyrics_path": str(lyrics),
                "songwriter_id": "writer-1",
                "primary_tag": "pop",
                "language_profile": "en-US",
                "split": "calibration",
                "owner_score": 6.0,
                "annotations": [
                    {"annotator_id": "owner", "score": 6.0, "disputed": False},
                    {"annotator_id": "reviewer-a", "score": 7.0, "disputed": True},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert analyze_manifest(manifest, output) == 0
    raw_output = output.read_text(encoding="utf-8")
    record = json.loads(raw_output)
    assert "A private line" not in raw_output
    assert record["annotation_summary"] == {
        "count": 2,
        "disputed": True,
        "mean_score": 6.5,
        "pairwise_mae": 1.0,
        "score_range": 1.0,
    }


def test_validation_reports_metrics_without_source_lyrics(tmp_path: Path) -> None:
    results = tmp_path / "results.jsonl"
    records = []
    for profile in ("en-US", "en-GB"):
        for index in range(3):
            score = 5.0 + index
            records.append(
                {
                    "id": f"{profile}-{index}",
                    "split": "holdout",
                    "language_profile": profile,
                    "score": score,
                    "owner_score": score,
                    "detected_pairs": [
                        {"left_line": 0, "right_line": 1, "rhyme_type": "exact"}
                    ],
                    "gold_pairs": [
                        {"left_line": 0, "right_line": 1, "rhyme_type": "exact"}
                    ],
                }
            )
    results.write_text(
        "".join(json.dumps(record) + "\n" for record in records), encoding="utf-8"
    )

    exit_code, report = validate_results(results)
    assert exit_code == 0
    assert report["exact_f1"] == 1.0
    assert report["accepted_macro_f1"] == {"en-GB": 1.0, "en-US": 1.0}
    assert report["spearman"] == 1.0
    assert report["owner_score_mae"] == 0.0


def test_calibration_requires_and_exports_ten_texts_per_tag(tmp_path: Path) -> None:
    results = tmp_path / "results.jsonl"
    output = tmp_path / "anchors.json"
    component_keys = (
        "phonetic_strength",
        "rhyme_density_and_coverage",
        "construction_complexity",
        "family_and_lexical_diversity",
        "scheme_and_section_development",
    )
    records = []
    for tag in ("rap", "pop", "rnb", "rock", "country", "electronic"):
        for index in range(10):
            records.append(
                {
                    "id": f"{tag}-{index}",
                    "split": "calibration",
                    "status": "evaluated",
                    "primary_tag": tag,
                    "metrics": {
                        f"raw_component_{key}": index / 10 for key in component_keys
                    },
                    "versions": {"formula_version": "english-rhymes-score-0.1.0"},
                }
            )
    results.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )

    assert calibrate_results(results, output) == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["sample_counts"] == {
        "country": 10,
        "electronic": 10,
        "pop": 10,
        "rap": 10,
        "rnb": 10,
        "rock": 10,
    }
    assert payload["profiles"]["rap"]["phonetic_strength"] == [0.18, 0.45, 0.72]


def test_exact_holdout_gate_ignores_internal_exact_pairs(tmp_path: Path) -> None:
    results = tmp_path / "results.jsonl"
    records = []
    for profile in ("en-US", "en-GB"):
        for index in range(3):
            records.append(
                {
                    "id": f"{profile}-{index}",
                    "split": "holdout",
                    "language_profile": profile,
                    "score": 5 + index,
                    "owner_score": 5 + index,
                    "detected_pairs": [
                        {
                            "left_line": 0,
                            "right_line": 0,
                            "rhyme_type": "exact",
                            "position": "internal",
                        }
                    ],
                    "gold_pairs": [
                        {
                            "left_line": 0,
                            "right_line": 1,
                            "rhyme_type": "exact",
                            "position": "line_end",
                        }
                    ],
                }
            )
    results.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )

    exit_code, report = validate_results(results)
    assert exit_code == 1
    assert report["exact_f1"] == 0.0
