"""Command-line interface for local Mixing analysis and profile research."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .audio import SoundFileDecoder
from .models import PrimaryGenre
from .pipeline import analyze_mixing
from .profiles import (
    ProfileObservation,
    ProfileReleaseEvidence,
    build_genre_profile,
    load_observations,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="secondear-mixing")
    commands = parser.add_subparsers(dest="command", required=True)

    analyze = commands.add_parser("analyze", help="Analyze a lossless stereo master")
    analyze.add_argument("audio", type=Path)
    analyze.add_argument(
        "--genre", required=True, choices=[item.value for item in PrimaryGenre]
    )
    analyze.add_argument("--reference", type=Path)
    analyze.add_argument("--profiles", type=Path)
    analyze.add_argument("--pretty", action="store_true")

    observe = commands.add_parser(
        "observe", help="Emit one rights-confirmed JSONL corpus observation"
    )
    observe.add_argument("audio", type=Path)
    observe.add_argument(
        "--genre", required=True, choices=[item.value for item in PrimaryGenre]
    )
    observe.add_argument("--track-id", required=True)
    observe.add_argument("--artist-id", required=True)
    observe.add_argument("--substyle", required=True)
    observe.add_argument("--period", required=True)
    observe.add_argument(
        "--split", required=True, choices=["calibration", "validation", "holdout"]
    )
    observe.add_argument("--rights-confirmed", action="store_true", required=True)

    profile = commands.add_parser(
        "build-profile", help="Build a profile from JSONL observations"
    )
    profile.add_argument("observations", type=Path)
    profile.add_argument("output", type=Path)
    profile.add_argument("--version", required=True)
    profile.add_argument("--release", action="store_true")
    profile.add_argument("--ebu-passed", action="store_true")
    profile.add_argument("--validation-passed", action="store_true")
    profile.add_argument("--holdout-passed", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "analyze":
        result = analyze_mixing(
            args.audio,
            args.genre,
            args.reference,
            profiles_path=args.profiles,
        )
        print(
            json.dumps(
                result.to_dict(), indent=2 if args.pretty else None, sort_keys=True
            )
        )
        return 0 if result.status.value == "evaluated" else 2

    if args.command == "observe":
        result = analyze_mixing(args.audio, args.genre)
        if result.separator is None or result.source_sha256 is None:
            print(json.dumps(result.to_dict(), sort_keys=True))
            return 2
        audio = SoundFileDecoder().decode(args.audio)
        observation = ProfileObservation(
            track_id=args.track_id,
            artist_id=args.artist_id,
            genre=PrimaryGenre(args.genre),
            substyle=args.substyle,
            period=args.period,
            split=args.split,
            rights_confirmed=args.rights_confirmed,
            source_format=audio.source_format,
            audio_sha256=result.source_sha256,
            analysis_version=result.analysis_version,
            formula_version=result.formula_version,
            analyzer_versions=result.analyzer_versions,
            metrics={metric.key: metric.value for metric in result.metrics},
            separator=result.separator,
        )
        print(json.dumps(observation.to_dict(), sort_keys=True))
        return 0

    observations = load_observations(args.observations)
    profile = build_genre_profile(
        observations,
        version=args.version,
        release=args.release,
        release_evidence=ProfileReleaseEvidence(
            ebu_passed=args.ebu_passed,
            validation_passed=args.validation_passed,
            holdout_passed=args.holdout_passed,
        ),
    )
    profile.save(args.output)
    print(json.dumps(profile.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
