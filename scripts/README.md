# Scripts

Repository scripts are reproducible, non-interactive where practical, and safe to run repeatedly.

`rhymes_research.py` analyzes a lawful private JSONL corpus without copying source lyrics into its
output and validates derived results against the published holdout targets:

```bash
PYTHONPATH=.:packages/analysis/src python3 scripts/rhymes_research.py analyze \
  research-data/private-manifest.jsonl research-data/derived-results.jsonl

PYTHONPATH=.:packages/analysis/src python3 scripts/rhymes_research.py calibrate \
  research-data/derived-results.jsonl research-data/owner-pilot-anchors.json

PYTHONPATH=.:packages/analysis/src python3 scripts/rhymes_research.py validate \
  research-data/derived-results.jsonl --split holdout --annotation-stage multi
```

The manifest validator rejects songwriter leakage across calibration, validation, and holdout
splits. See `research-data/README.md` for the local record format.
