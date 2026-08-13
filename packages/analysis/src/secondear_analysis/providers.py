"""Boundaries for future licensed lyrics providers."""

from __future__ import annotations

from typing import Protocol


class LyricsProvider(Protocol):
    """A provider may return lyrics only under an explicit content license."""

    @property
    def provider_id(self) -> str: ...

    def fetch_lyrics(self, source_reference: str) -> str:
        """Fetch licensed lyrics without persisting them."""
        ...


class ProviderUnavailableError(RuntimeError):
    """Raised when no licensed lyrics provider is configured."""


def fetch_lyrics(_source_reference: str) -> str:
    """Reject network lyrics retrieval in the default open-source build."""

    raise ProviderUnavailableError(
        "No licensed lyrics provider is configured. Paste or upload lyrics you may analyze."
    )
