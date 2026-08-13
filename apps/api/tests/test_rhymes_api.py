from __future__ import annotations

from fastapi.testclient import TestClient
from secondear_api.main import app

client = TestClient(app)


def test_rhymes_endpoint_returns_versioned_evidence() -> None:
    lyrics = """I carry the flame while I walk through the night
I follow the name and I hold to the light
I write every line and I keep the words bright
I turn every sign till the timing is right
We stand in the rain with a map in our hand
We plan it again as we cross through the land
We mark every grain and we build where we stand
We start with a chain and we finish as planned"""
    response = client.post(
        "/v1/rhymes/analyze",
        json={
            "lyrics": lyrics,
            "language_profile": "en-US",
            "primary_tag": "pop",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["criterion"] == "rhymes"
    assert body["status"] == "evaluated"
    assert body["versions"]["formula_version"] == "english-rhymes-score-0.1.0"
    assert len(body["versions"]["dictionary_sha256"]) == 64
    assert body["input_summary"]["unique_lines"] == 8
    assert len(body["lines"]) == 8
    assert body["pairs"]
    assert body["chains"]


def test_api_rejects_unknown_fields() -> None:
    response = client.post(
        "/v1/rhymes/analyze",
        json={
            "lyrics": "A valid line",
            "language_profile": "en-US",
            "primary_tag": "pop",
            "download_from_genius": True,
        },
    )
    assert response.status_code == 422


def test_api_returns_insufficient_data_without_a_zero_score() -> None:
    response = client.post(
        "/v1/rhymes/analyze",
        json={
            "lyrics": "night light",
            "language_profile": "en-US",
            "primary_tag": "rap",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_data"
    assert response.json()["score"] is None


def test_api_returns_pronunciation_review_choices() -> None:
    response = client.post(
        "/v1/rhymes/analyze",
        json={
            "lyrics": "We write every line and end with read",
            "language_profile": "en-US",
            "primary_tag": "rock",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "needs_pronunciation_review"
    issue = next(issue for issue in body["pronunciation_issues"] if issue["normalized"] == "read")
    assert issue["blocks_score"] is True
    assert len(issue["choices"]) >= 2


def test_api_enforces_the_utf8_byte_limit() -> None:
    response = client.post(
        "/v1/rhymes/analyze",
        json={
            "lyrics": "é" * 131_073,
            "language_profile": "en-US",
            "primary_tag": "pop",
        },
    )

    assert response.status_code == 422
    assert "262144-byte limit" in response.json()["detail"]
