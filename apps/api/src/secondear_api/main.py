"""Thin synchronous FastAPI transport for SecondEar analyzers."""

from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from secondear_analysis.domain import PronunciationOverride, RhymeAnalysisRequest
from secondear_analysis.rhyme_analyzer import analyze_rhymes

from secondear_api.schemas import (
    RhymeAnalysisInput,
    RhymeAnalysisOutput,
    result_to_output,
)

app = FastAPI(
    title="SecondEar API",
    description="Evidence-based music analysis without persistence.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "SECONDEAR_WEB_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/v1/rhymes/analyze",
    response_model=RhymeAnalysisOutput,
    tags=["rhymes"],
)
def analyze_rhyme_request(payload: RhymeAnalysisInput) -> RhymeAnalysisOutput:
    """Analyze caller-provided lyrics without logging or retaining their text."""

    try:
        result = analyze_rhymes(
            RhymeAnalysisRequest(
                lyrics=payload.lyrics,
                language_profile=payload.language_profile,
                primary_tag=payload.primary_tag,
                pronunciation_overrides=tuple(
                    PronunciationOverride(
                        target=override.target,
                        pronunciation=override.pronunciation,
                    )
                    for override in payload.pronunciation_overrides
                ),
                source_reference=payload.source_reference,
            )
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    return result_to_output(result)
