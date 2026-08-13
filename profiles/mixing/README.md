# Mixing profiles

Released genre profiles belong in this directory as versioned JSON documents. The repository does
not currently contain a released profile.

Do not hand-author target ranges. Use `secondear-mixing observe` and
`secondear-mixing build-profile` with lawfully obtained WAV/FLAC masters. Audio files, Demucs weights,
and source-identifying corpus content must not be committed.

A released profile requires at least 30 calibration, 10 validation, and 10 holdout observations for
one genre, no more than two tracks per artist, more than one represented substyle and period,
consistent analyzer and model identities, official EBU conformance, and passed validation and holdout
gates. See `docs/MIXING.md`.
