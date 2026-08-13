from __future__ import annotations

from secondear_analysis.text import parse_lyrics


def test_parser_preserves_offsets_and_deduplicates_repeated_sections() -> None:
    lyrics = """[Verse 1]
First line here
Second line there

[Chorus]
We rise tonight
We hold the light

[Chorus]
We rise tonight
We hold the light
"""
    document = parse_lyrics(lyrics)

    assert document.total_sections == 3
    assert len(document.sections) == 2
    assert document.repeated_sections == 1
    chorus = document.sections[1]
    assert chorus.occurrence_count == 2
    first_token = chorus.lines[0].tokens[0]
    assert lyrics[first_token.span.start : first_token.span.end] == "We"


def test_parser_normalizes_apostrophes_without_changing_source_text() -> None:
    lyrics = "I can’t change the original line"
    document = parse_lyrics(lyrics)
    token = document.sections[0].lines[0].tokens[1]

    assert token.text == "can’t"
    assert token.normalized == "can't"
    assert lyrics[token.span.start : token.span.end] == "can’t"


def test_parser_keeps_contractions_as_dictionary_tokens_and_ignores_punctuation() -> None:
    lyrics = "(We're) ready — aren't we?"
    document = parse_lyrics(lyrics)
    tokens = document.sections[0].lines[0].tokens

    assert [token.normalized for token in tokens] == ["we're", "ready", "aren't", "we"]
    assert [lyrics[token.span.start : token.span.end] for token in tokens] == [
        "We're",
        "ready",
        "aren't",
        "we",
    ]
