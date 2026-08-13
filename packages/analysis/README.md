# Analysis Package

This directory is reserved for the framework-independent Python analysis engine and its domain
models. It must remain callable without FastAPI, a frontend, a database, or an external AI service.

The decoder and concrete model libraries remain open decisions. See `docs/DECISIONS.md`.
