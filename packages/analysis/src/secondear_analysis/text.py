"""Lyrics parsing with stable source coordinates and section deduplication."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from secondear_analysis.domain import SourceSpan

SECTION_HEADER = re.compile(
    r"^\s*\[(?P<label>(?:verse|chorus|bridge|pre[- ]?chorus|intro|outro|hook|refrain|break)[^]]*)]\s*$",
    re.IGNORECASE,
)
TOKEN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*")


@dataclass(frozen=True, slots=True)
class Token:
    id: str
    text: str
    normalized: str
    section_index: int
    line_index: int
    index_in_line: int
    span: SourceSpan
    is_line_ending: bool


@dataclass(frozen=True, slots=True)
class Line:
    section_index: int
    line_index: int
    text: str
    span: SourceSpan
    tokens: tuple[Token, ...]


@dataclass(frozen=True, slots=True)
class Section:
    index: int
    label: str
    occurrence_count: int
    lines: tuple[Line, ...]


@dataclass(frozen=True, slots=True)
class LyricsDocument:
    sections: tuple[Section, ...]
    total_sections: int
    total_lines: int
    repeated_sections: int


@dataclass(slots=True)
class _SectionDraft:
    label: str
    raw_lines: list[tuple[int, int, str]]


def normalize_token(value: str) -> str:
    """Return the stable dictionary lookup form for an English token."""

    normalized = unicodedata.normalize("NFKC", value).replace("’", "'")
    return normalized.casefold()


def _section_key(draft: _SectionDraft) -> tuple[str, ...]:
    return tuple(" ".join(normalize_token(match.group()) for match in TOKEN.finditer(text)) for _, _, text in draft.raw_lines)


def parse_lyrics(lyrics: str) -> LyricsDocument:
    """Parse line-broken lyrics and collapse exact repeated sections.

    Source offsets always refer to ``lyrics`` and are never computed from a
    normalized copy.
    """

    drafts: list[_SectionDraft] = []
    current = _SectionDraft(label="Section 1", raw_lines=[])
    next_default = 2
    cursor = 0

    for raw_with_newline in lyrics.splitlines(keepends=True):
        raw = raw_with_newline.rstrip("\r\n")
        line_start = cursor
        cursor += len(raw_with_newline)
        header = SECTION_HEADER.match(raw)
        if header:
            if current.raw_lines:
                drafts.append(current)
            current = _SectionDraft(label=header.group("label").strip(), raw_lines=[])
            continue
        if not raw.strip():
            if current.raw_lines:
                drafts.append(current)
                current = _SectionDraft(label=f"Section {next_default}", raw_lines=[])
                next_default += 1
            continue
        if TOKEN.search(raw):
            current.raw_lines.append((len(drafts), line_start, raw))

    if current.raw_lines:
        drafts.append(current)

    total_lines = sum(len(draft.raw_lines) for draft in drafts)
    key_to_index: dict[tuple[str, ...], int] = {}
    unique: list[tuple[_SectionDraft, int]] = []
    for draft in drafts:
        key = _section_key(draft)
        existing = key_to_index.get(key)
        if existing is None:
            key_to_index[key] = len(unique)
            unique.append((draft, 1))
        else:
            first, count = unique[existing]
            unique[existing] = (first, count + 1)

    sections: list[Section] = []
    global_line = 0
    for section_index, (draft, occurrence_count) in enumerate(unique):
        lines: list[Line] = []
        for _, line_start, text in draft.raw_lines:
            matches = list(TOKEN.finditer(text))
            tokens = tuple(
                Token(
                    id=f"s{section_index}.l{global_line}.t{token_index}",
                    text=match.group(),
                    normalized=normalize_token(match.group()),
                    section_index=section_index,
                    line_index=global_line,
                    index_in_line=token_index,
                    span=SourceSpan(
                        line_index=global_line,
                        start=line_start + match.start(),
                        end=line_start + match.end(),
                    ),
                    is_line_ending=token_index == len(matches) - 1,
                )
                for token_index, match in enumerate(matches)
            )
            lines.append(
                Line(
                    section_index=section_index,
                    line_index=global_line,
                    text=text,
                    span=SourceSpan(global_line, line_start, line_start + len(text)),
                    tokens=tokens,
                )
            )
            global_line += 1
        sections.append(
            Section(
                index=section_index,
                label=draft.label,
                occurrence_count=occurrence_count,
                lines=tuple(lines),
            )
        )

    return LyricsDocument(
        sections=tuple(sections),
        total_sections=len(drafts),
        total_lines=total_lines,
        repeated_sections=max(0, len(drafts) - len(sections)),
    )
