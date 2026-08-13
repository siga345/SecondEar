# Private Rhymes Research Data

This directory is intentionally ignored except for documentation and the synthetic manifest example.
Put lawfully obtained lyrics outside version control and reference them from a local JSONL manifest.
The research command writes only hashes, annotations, and derived analysis results.

Do not commit commercial lyrics, Genius transcriptions, audio, API credentials, or personally
identifying annotator information.

## Manifest record

```json
{
  "id": "local-track-001",
  "lyrics_path": "research-data/private/local-track-001.txt",
  "songwriter_id": "writer-group-001",
  "primary_tag": "pop",
  "language_profile": "en-US",
  "split": "calibration",
  "owner_score": 7.5,
  "annotations": [
    {"annotator_id": "owner", "score": 7.5, "disputed": false, "dispute_codes": []},
    {"annotator_id": "reviewer-a", "score": 7.0, "disputed": false, "dispute_codes": []},
    {"annotator_id": "reviewer-b", "score": 6.5, "disputed": true, "dispute_codes": ["near-rhyme-boundary"]}
  ],
  "recognition_cohort": null,
  "gold_pairs": [
    {"left_line": 0, "right_line": 1, "rhyme_type": "exact", "position": "line_end"}
  ]
}
```

Use stable pseudonymous songwriter and annotator identifiers. A writer group may occur in only one
split. Derived output preserves individual scores, dispute codes, score range, and pairwise mean
absolute disagreement without copying annotation prose or source lyrics.

After analysis, use the `calibrate` command to derive versioned 20th/50th/80th component anchors.
It refuses to run until every primary tag has at least ten evaluated calibration texts. Calibration
output contains only aggregate derived values.
