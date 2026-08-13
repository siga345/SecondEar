# SecondEar

SecondEar is an open-source objective music analysis system for artists, producers, and engineers.
It uses digital signal processing, music information retrieval, and computational analysis to give
musicians an independent, evidence-based view of their own tracks.

> **No taste. No attachment. Just evidence.**

## Project status

SecondEar is in its initial architecture and technical decision phase. The repository currently
contains the project boundaries, proposed monorepo structure, analytical data model, roadmap, and
open implementation decisions. It does not contain a working audio analyzer yet.

The first planned vertical slice is intentionally small:

```text
Audio upload
  -> validation
  -> decoding
  -> duration, sample rate, and channel count
  -> typed API result
  -> web display
```

No scoring, subjective evaluation, AI opinion, persistence, authentication, or advanced DSP belongs
in this slice.

## Repository map

```text
SecondEar/
├── apps/
│   ├── api/                 # Planned FastAPI transport layer
│   └── web/                 # Planned Next.js analytical interface
├── packages/
│   └── analysis/            # Framework-independent analysis engine
├── docs/
│   ├── PRODUCT.md
│   ├── ARCHITECTURE.md
│   ├── ANALYSIS_MODEL.md
│   ├── DECISIONS.md
│   └── ROADMAP.md
├── fixtures/                # Synthetic and redistributable test audio
├── scripts/                 # Development and maintenance commands
├── tests/                   # Cross-package and end-to-end tests
└── AGENTS.md                # Durable project rules for coding agents
```

## Contributing at this stage

Start with [AGENTS.md](AGENTS.md), then read the documents in `docs/`. During the current phase,
contributions should clarify requirements, compare implementation options, or improve architecture
without prematurely selecting libraries or adding production code.

Runtime setup, development commands, CI, and dependency installation instructions will be added when
the first implementation choices are accepted. The open-source license is also intentionally pending
an explicit project decision.
