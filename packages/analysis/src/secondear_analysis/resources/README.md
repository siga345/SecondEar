# Pronunciation Resources

This directory contains pinned upstream pronunciation data used offline by the English Rhymes
analyzer. The analyzer parses the source formats directly; it does not use the GPL-licensed Python
`cmudict` wrapper.

- `cmudict-0.7b-2026-08-14.dict`: CMU Pronouncing Dictionary, downloaded from the official
  `cmusphinx/cmudict` repository and used under its unrestricted-use notice.
- `britfone.main.3.0.1.csv`: Britfone 3.0.1, used under the MIT License.

Exact SHA-256 fingerprints are returned with every analysis and checked by tests.
The complete upstream license texts are distributed beside the data files.
