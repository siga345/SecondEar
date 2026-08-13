# SecondEar 90-Point Methodology

**Status:** Draft methodology 0.1

**Implementation status:** Mixing v1 engine implemented; no public profiles released

**Last updated:** 2026-08-14

This document defines the first methodological version of the SecondEar 90-point model. It describes
what each criterion is intended to represent and which evidence may support it. It does not yet lock
the final formulas, weights, thresholds, genre profiles, or software dependencies.

## Purpose

SecondEar may issue direct critical conclusions, including identifying weak structure, repetitive
rhythmic design, unstable vocal execution, or technical mix problems. Such conclusions are valid only
when they are derived from published criteria and traceable evidence.

The system does not simulate personal taste. It must not use enjoyment, emotional attachment,
listener preference, vibe, or an untraceable model opinion as evidence.

The distinction is:

```text
Unsupported: "The track is boring because it feels repetitive."

Supported: "The track has a high structural-monotony indicator because three repeated sections
have a mean feature similarity of 0.93 and show limited changes in onset density, spectral profile,
and arrangement density."
```

## Common score semantics

All nine criteria use the same ordinal scale. Numeric thresholds must eventually be defined per
criterion and genre profile.

| Score | Meaning within the criterion model |
| ---: | --- |
| 10 | Exceptional result across the formalized and applicable parameters |
| 9 | Very strong result with isolated limitations |
| 8 | Strong result |
| 7 | Reliably above the established baseline |
| 6 | Functional result with noticeable limitations |
| 5 | Middle of the applicable comparison range |
| 4 | Several systematic limitations |
| 3 | Weak result |
| 2 | Serious, repeated problems |
| 1 | The criterion is barely realized under the applicable model |

A score of 10 does not mean that the software likes the work. It means that the work lies in the
upper region of the declared criterion model and comparison profile.

The nominal maximum is 90 points:

```text
Rhymes                  10
Imagery                 10
Structure               10
Rhythm                  10
Artist Performance      10
Mixing                  10
Sound Production        10
Individuality           10
Charisma                 10
                       ---
Overall                  90
```

An overall score may be produced only when the applicability policy permits it. Missing criteria
must not silently be replaced with zero or rescaled without a documented rule.

## Criterion result contract

Each criterion analyzer must eventually return:

- criterion key and public label;
- score and scale;
- confidence, represented independently from the score;
- applicability status;
- evidence types;
- sub-scores or contributing features;
- genre profile and comparison corpus version;
- analyzer and formula versions;
- supporting metrics and findings;
- known limitations that affected the result.

No single LLM or black-box request may assign any of the nine criterion scores. Statistical or ML
components may estimate bounded intermediate features, but the score must be derived through a
versioned, inspectable mechanism.

## Genre normalization

Complexity is not quality. Density, precision, variation, and deviation have different functions in
different genres. Every criterion must distinguish universal technical failures from genre-relative
expectations.

The initial product will ask the user to choose a core genre. More detailed subgenres may be added
after the core profiles are validated. The taxonomy and fallback behavior for mixed or unsupported
genres remain open decisions.

## Criterion boundary rules

Several criteria reuse the same extracted features. Reuse is allowed, but the analytical question and
score contribution must remain distinct. A metric must not reward the same property twice under two
different labels.

| Boundary | First criterion asks | Second criterion asks |
| --- | --- | --- |
| Rhythm / Artist Performance | How is the rhythmic material designed? | How deliberately and consistently is the vocal rhythm executed? |
| Structure / Sound Production | How are macro sections organized and related? | How do instrumental layers and sonic roles develop inside that organization? |
| Artist Performance / Charisma | How controlled and technically stable is the vocal execution? | How broad, deliberate, and repeatable is the expressive variation? |
| Mixing / Sound Production | How technically well are sources integrated in the final signal? | How are the sources selected, arranged, and developed? |
| Imagery / Individuality | What imagery and figurative devices occur in this text? | How distinctive and stable are lyrical traits relative to the corpus and artist catalog? |

For example, phrase timing may support both Artist Performance and Charisma. Artist Performance may
use unexplained timing error and consistency, while Charisma may use controlled section contrast and
repeatable anticipation patterns. The formulas must not apply the same raw variance in the same way
to both scores.

## 1. Rhymes

**Internal meaning:** phonetic and rhyme construction.

### Definition

The Rhymes criterion evaluates the construction of phonetic relationships between line endings and
internal positions. It evaluates development, variety, complexity, consistency, and genre-relative
appropriateness rather than poetic beauty.

### Inputs and shared analyzers

- submitted lyrics and declared language;
- vocal audio when available;
- phoneme and syllable representation;
- stress detection;
- lyric-to-audio alignment;
- beat grid and section boundaries;
- genre profile and lyrical comparison corpus.

### Initial English-language scope

North American English (`en-US`) is the first supported language profile. This is a language-support
decision, not a claim that rhyme matters more or less in English than in other languages. The
analyzer contract remains language-neutral, while pronunciation, phoneme similarity, morphology,
and corpus expectations belong to versioned language profiles. Russian support may be added later
and must not reuse English thresholds or phoneme costs without validation.

The first implementation stage is text-only and accepts manually submitted, line-broken lyrics. It
uses a versioned CMU Pronouncing Dictionary file and accepts explicit pronunciation overrides for
names, slang, contractions, dialect forms, and other out-of-vocabulary tokens. It does not infer
lyrics from audio or claim that a dictionary pronunciation is identical to the performed vocal.
Audio alignment, performed-pronunciation correction, cross-line internal rhyme, and code-switching
remain later stages.

The initial detector exposes evidence before producing a score:

1. normalize text while preserving line and section boundaries;
2. resolve all documented pronunciation variants and lexical stress;
3. extract rhyme zones from the primary stressed vowel and following phonemes;
4. compare rhyme zones with a documented, feature-weighted phoneme distance;
5. distinguish exact, approximate, and identity rhyme relations;
6. group pairwise matches into rhyme families, line-ending schemes, and chains;
7. return metrics, uncertainty, analyzer versions, dictionary identity, and source spans.

Exact spelling or unweighted edit distance over letters is insufficient because English spelling
does not reliably encode pronunciation and phoneme substitutions are not equally perceptible. When
a token has multiple dictionary pronunciations, the text-only detector reports the best supported
candidate and reduces confidence rather than claiming to know the performed variant.

For the text-only stage, line, token, and syllable counts are `measured`; pronunciations and rhyme
relations are `estimated`; density, family, scheme, and chain metrics are `derived`; and future
corpus-relative predictability will be `benchmarked`. A criterion score remains unavailable until an
English annotation protocol, genre profiles, comparison corpus, formula, and validation thresholds
are accepted.

### Candidate components

- rhyme density relative to lines and syllables;
- mean phonetic match length and similarity;
- multisyllabic, internal, and line-ending rhyme rates;
- diversity of rhyme families;
- longest and typical rhyme-chain lengths;
- rhyme-scheme consistency;
- information value of rhyme pairs relative to the corpus;
- same-word, same-lemma, and same-grammatical-ending rates;
- penalties for excessive mechanical reuse or highly predictable pairs.

The scoring weights must vary by genre. Technical rap may reward dense internal and multisyllabic
construction, while pop, punk, singer-songwriter, or spoken-word profiles may require different
expectations.

Repeated words, identical rhyme zones, and highly common rhyme families must remain visible instead
of receiving the same eventual credit as diverse construction. Repetition used as a refrain must
also remain distinguishable from accidental or mechanical reuse.

### Initial anchors

- **10:** high genre-relative density, diverse schemes, complex construction, and limited mechanical
  repetition.
- **7:** stable and varied rhyme construction, primarily using simpler devices.
- **5:** a functional basic system dominated by line endings and limited variety.
- **3:** sparse, accidental, highly repetitive, or frequently weak phonetic relationships.

### Confidence and applicability

Confidence depends on language support, phoneme quality, alignment quality, vocal intelligibility,
and the effects of unusual pronunciation, code-switching, mumbling, pitch correction, or formant
processing. Instrumentals, insufficient text, unsupported languages, or failed alignment may result
in `insufficient_data`.

### User evidence and limitations

The report should highlight detected rhymes and show density, multisyllabic and internal rhyme rates,
diversity, and chain length. Intentional simplicity may be a valid artistic choice; the criterion
measures rhyme construction under the selected profile, not the quality of poetry as a whole.

### Initial research references

These sources inform the research direction but do not yet define the scoring formula:

- [CMU Pronouncing Dictionary](https://github.com/cmusphinx/cmudict)
- [Detecting Rhyming Words](https://repository.tudelft.nl/record/uuid%3A31a34297-aa48-4f02-aa78-e45389a7c779)
- [Supervised Rhyme Detection with Siamese Recurrent Networks](https://aclanthology.org/W18-4509/)
- [Discovering Lexical Similarity Through Articulatory Feature-based Phonetic Edit Distance](https://arxiv.org/abs/2008.06865)

## 2. Imagery

**Internal meaning:** linguistic imagery and figurative construction.

### Definition

The Imagery criterion estimates the use of concrete, specific, figurative, and statistically
distinct language instead of relying exclusively on abstract or highly conventional statements. It
does not claim to measure beauty, depth, or emotional meaning.

### Inputs and shared analyzers

- submitted lyrics, declared language, and section structure;
- part-of-speech and dependency analysis;
- named-entity and semantic-role extraction;
- concreteness and imageability resources;
- metaphor and simile estimators;
- semantic embeddings, lexical frequency data, and a genre-language corpus.

### Candidate components

- concrete sensory language: objects, places, colors, sounds, physical actions, and bodily details;
- metaphor, simile, and figurative-construction density;
- semantic specificity;
- recurring motif detection and development across sections;
- lexical and phrase-combination novelty;
- figurative-device diversity;
- cliché and high-frequency-template rate.

### Initial anchors

- **10:** high specificity and imagery, developed motifs, varied devices, and low genre-relative
  cliché density.
- **7:** several clear image constructions and generally specific language.
- **5:** predominantly direct language with isolated images.
- **3:** predominantly abstract or highly conventional constructions under the applicable lyrical
  profile.

### Confidence and applicability

Confidence will usually be lower than for phonetic or signal measurements. It depends on language,
text length, parser quality, corpus coverage, and the accuracy of figurative-language estimators.
Short lyrics and unsupported languages may produce `insufficient_data`.

### User evidence and limitations

The report should cite the exact lines supporting concrete language, metaphors, motifs, novelty, and
cliché findings. The primary risk is mistaking intentional minimalism for weak writing. Genre and
lyrical-style normalization are mandatory.

## 3. Structure

**Internal meaning:** structural organization and development.

### Definition

The Structure criterion evaluates whether a composition demonstrates organized, distinguishable,
and controlled macrostructure under the selected genre profile. Non-standard structure is not a
defect by itself.

### Inputs and shared analyzers

- full mix and optional stems;
- beat and downbeat positions;
- anonymous section segmentation;
- self-similarity representation;
- harmony, loudness, timbre, and onset-density timelines.

### Candidate components

- section-boundary strength and segmentation confidence;
- separability of sections when the genre expects contrast;
- repetition balance;
- measurable development in repeated sections;
- transition discontinuities in loudness, harmony, spectrum, and rhythm;
- macro-dynamic shape;
- section duration and proportional balance;
- structural economy, only after a defensible operational definition exists.

### Initial anchors

- **10:** clearly controlled organization, genre-appropriate repetition and development, and no
  unexplained technical discontinuities.
- **7:** clear functional structure with limited development of repeated material.
- **5:** functional but strongly repetitive or fragmented structure relative to the selected profile.
- **3:** weak or chaotic relationships between sections under the applicable model.

### Confidence and applicability

Confidence depends on beat tracking, segmentation, and feature quality. Very short pieces and styles
for which segmentation is unreliable may be unevaluated. Early versions should use anonymous labels
such as A, B, and C rather than asserting verse or chorus labels without sufficient evidence.

### User evidence and limitations

The report should show section intervals, a self-similarity view, repeated-section similarities, and
the features supporting development or monotony findings. Segmentation systems can fail outside the
musical traditions represented by their evaluation data.

## 4. Rhythm

**Internal meaning:** rhythmic design and controlled variation.

### Definition

The Rhythm criterion evaluates the compositional rhythmic system. It is distinct from Vocal
Performance, which evaluates how accurately and deliberately the artist realizes that system.

### Inputs and shared analyzers

- full mix and, when available, separated vocal and percussion signals;
- beat, downbeat, meter, and onset estimates;
- lyric and syllable alignment;
- section boundaries and genre profile.

### Candidate components

- rhythmic-pattern diversity and repetition;
- onset density and section-level density contrast;
- syncopation and accent distribution;
- phrase-length and subdivision diversity;
- rest and pause placement;
- section-level rhythmic differentiation;
- vocal-to-beat relationships, with delivery accuracy attributed to Artist Performance.

### Initial anchors

- **10:** high genre-relative control, variation, and coherent rhythmic design.
- **7:** a stable system with several meaningful variations.
- **5:** a functional design dominated by one pattern.
- **3:** unstable or poorly organized metric relationships under the selected profile.

### Confidence and limitations

Confidence depends on beat, meter, onset, and source-separation estimates. Greater complexity or
syncopation is not automatically better; genre-relative control is the target.

## 5. Artist Performance

**Internal key:** `vocal_performance`.

**Internal meaning:** technical control of the vocal or rap performance only.

Instrumental execution is outside this criterion and belongs to Sound Production under the current
SecondEar taxonomy.

### Inputs and shared analyzers

- submitted lyrics;
- isolated vocal where available, otherwise an estimated vocal stem;
- lyric, phoneme, and syllable alignment;
- pitch and vocal-activity tracking;
- beat grid and section boundaries;
- declared vocal mode and genre profile.

### Candidate components

- pitch control, drift, transitions, vibrato, and register behavior for pitched vocals;
- timing control, onset deviation, phrase timing, and intentional microtiming;
- phrase-level dynamics, accents, and section contrast;
- timbral control and register transitions;
- articulation and intelligibility;
- breath and pause behavior when reliably detectable;
- delivery variation between sections and repeated phrases.

Weights must depend on vocal mode. Pitch accuracy has little relevance to many rap performances,
while pitch, vibrato, and dynamics have a larger role in operatic or conventionally pitched singing.
Stylistic roughness and micro-pitch deviation must not automatically be treated as errors.

### Initial anchors

- **10:** high technical control with broad, deliberate variation and stability where required.
- **7:** controlled performance with limited variation or isolated instability.
- **5:** functional performance with recurring timing, pitch, dynamics, or articulation limitations.
- **3:** systematic instability under the applicable vocal profile.

### Confidence and limitations

Source-separation artifacts, effects, backing vocals, unusual timbre, unsupported language, and weak
alignment reduce confidence independently from the score. Failed speech recognition alone must not
be interpreted as poor articulation.

## 6. Mixing

**Internal meaning:** technical mix integrity.

### Definition

The Mixing criterion evaluates the technical integration of sources in the final stereo or master
signal through levels, dynamics, spectrum, spatial behavior, masking proxies, balance, and defects.

Mixing v1 is implemented as a deterministic, profile-based penalty engine. It evaluates the combined
result of mixing and mastering in one final stereo master. The complete operational contract and
formula are defined in `docs/MIXING.md`.

### Inputs and shared analyzers

- lossless WAV or FLAC, stereo, at least 44.1 kHz, from 30 through 600 seconds;
- one primary genre: `rap`, `pop`, `r_and_b`, `rock`, `country`, or `electronic`;
- full mix and Demucs `htdemucs_ft` estimates for `vocals`, `drums`, `bass`, and `other`;
- time-dependent level, spectrum, stereo, and dynamics measurements;
- a released, version-matched genre profile and an optional non-scoring reference.

### Implemented penalty blocks

- element balance, maximum penalty 4.0: relative stem loudness, temporal ratio stability, and
  ERB-band audibility or masking proxies;
- stereo field, maximum penalty 3.0: L/R balance, correlation distribution, mid/side width by band,
  and mono fold-down;
- tonal balance, maximum penalty 2.5: relative energy in 24 ERB-spaced bands;
- loudness and dynamics, maximum penalty 2.0: gain-relative LUFS relationships, LRA, crest factor,
  peak-to-loudness relationship, and short-term variation;
- signal integrity, maximum penalty 2.0: sample/true peak, clipping, DC offset, and invalid data.

The score begins at 10 and subtracts the five block penalties, clamped to 1--10. The public value is
rounded half-up, while the continuous raw value is retained. For profile-relative features, values
inside Q10--Q90 receive no penalty; outside deviations are normalized with MAD. A block combines
`0.7 * worst severity + 0.3 * mean severity`.

Absolute integrated and short-term LUFS are retained as measurements and reference deltas but are not
penalty features. This keeps the score invariant under a uniform gain change while true peak remains
at or below `0 dBTP`; overload can still increase the fixed integrity penalty.

### Initial anchors

- **10:** no serious technical defects and stable behavior within the documented genre or reference
  distribution.
- **7:** strong technical integration with several measurable deviations.
- **5:** recurring limitations such as masking, unstable vocal balance, uncontrolled peaks, or
  compatibility problems.
- **3:** systematic problems that impair intelligibility or technical compatibility.

### Confidence and limitations

There is no universal ideal EQ, loudness, dynamics, or stereo width. A full Mixing score requires
lossless source material, reliable separation, confidence of at least `0.65`, and a released target
profile built from at least 30 calibration, 10 validation, and 10 holdout tracks. Estimated-stem
confidence is capped at `0.8`. Lossy research audio may support exploratory metrics but must not be
treated as equivalent evidence. The reference is comparison-only and cannot affect the target score.

## 7. Sound Production

**Internal meaning:** arrangement and sonic construction.

### Definition

The Sound Production criterion evaluates how instrumental, arrangement, and sound-design elements
are selected, assigned roles, layered, contrasted, and developed over time. It is deliberately
separate from final-mix technical integrity.

### Inputs and shared analyzers

- full mix and estimated or supplied stems;
- sections, beat grid, harmony, and timbral features;
- source activity and arrangement-density timelines;
- genre and production comparison corpus.

### Candidate components

- instrumentation and source-role estimates;
- layer density, redundancy, and activity;
- changes between repeated sections;
- instrumental, rhythmic, harmonic, spectral, and timbral development;
- sound-palette coherence and diversity;
- drops, breakdowns, fills, transitions, silence, and density shifts;
- repetition and loop transformation;
- functional arrangement roles such as rhythm, bass, harmony, melody, and texture.

### Initial anchors

- **10:** controlled layering, clear element functions, developed section changes, and a coherent
  timbral system.
- **7:** strong production with some underdeveloped repetitions.
- **5:** functional production with limited variation or density development.
- **3:** weak functional interaction or insufficient genre-relative arrangement development.

### Confidence and limitations

Minimalism must not be penalized automatically. Source separation and instrument-role estimation are
uncertain and may be genre-dependent. Complexity is evidence, not a score target.

## 8. Individuality

**Internal meaning:** statistical distinctiveness.

### Definition

The Individuality criterion estimates how the artist's measurable features differ from nearby genre
distributions and how consistently those features recur across the artist's own work. Distinctive
does not inherently mean good, but this methodology intentionally rewards a stable, statistically
distinguishable identity.

### Inputs and shared analyzers

- vocal, rhythmic, production, lyrical, and structural representations;
- a versioned genre and language corpus;
- multiple tracks by the artist when available;
- artist, track, and genre embeddings or explicit feature profiles.

### Candidate components

- vocal-timbre distinctiveness;
- rhythmic signature;
- production and sound-palette signature;
- lexical, syntactic, motif, and rhyme signature;
- structural preferences;
- distance from genre neighbors and centroid;
- within-artist consistency around an artist profile;
- agreement across several independent feature groups.

### Initial anchors

- **10:** substantial genre-relative distance, a stable cross-track signature, and distinctiveness in
  multiple independent feature groups.
- **7:** one or two clearly distinguishing and stable features.
- **5:** a mostly typical genre profile.
- **3:** strong similarity to the reference cluster without stable distinguishing characteristics.

### Confidence and limitations

A single track supports only a limited Track Distinctiveness estimate. Artist Individuality requires
multiple tracks, with confidence improving as catalog coverage grows. Corpus composition, culture,
language, genre labels, and embedding behavior can bias the result.

## 9. Charisma

**Internal key:** `expressive_delivery`.

**Internal meaning:** controlled expressive variation in vocal delivery.

### Definition

The criterion estimates controlled temporal, dynamic, pitch-related, and timbral variation in the
delivery of vocal material. It does not claim to measure whether a listener believes, likes, or feels
emotionally affected by the artist.

### Inputs and shared analyzers

- isolated or estimated vocal;
- lyrics and phrase alignment;
- pitch, dynamics, timbre, and timing contours;
- section and repetition structure;
- genre and vocal-mode profile.

### Candidate components

- phrase-level loudness variation, accents, and contrast;
- deliberate anticipation, delay, phrase endings, and pause placement;
- slides, bends, vibrato, and register transitions where applicable;
- brightness, breathiness, roughness, and other defensible timbral proxies;
- variation between repeated phrases;
- vocal differentiation between sections;
- expressive-event density;
- repeatable control of expressive patterns.

High variance alone is not expressive control. The conceptual relationship is:

```text
expressive delivery = variation combined with repeatable control
```

The implemented formula must define that relationship without multiplying arbitrary uncalibrated
features.

### Initial anchors

- **10:** broad but controlled variation across several applicable dimensions and clear section-level
  differentiation.
- **7:** controlled variation using a narrower range of techniques.
- **5:** stable but relatively uniform delivery.
- **3:** nearly uniform delivery or high random instability without repeatable control.

### Confidence and limitations

Weights depend on genre and vocal mode. Rap may emphasize timing, accents, pauses, and timbre; pop
singing may emphasize pitch, dynamics, register, and timbre; punk may weight timbre and dynamics more
than pitch stability. The criterion remains an estimate and requires carefully designed human
annotation for validation.

## Cross-criterion findings

Some user-facing conclusions require evidence from several criteria and must not be generated by a
single sub-score.

### Structural monotony

Candidate evidence includes repeated-section similarity, low onset-density variation, limited layer
changes, small spectral or dynamic changes, and repeated vocal-flow patterns.

### Limited chorus differentiation

Candidate evidence includes low contrast in loudness, spectrum, melody, onset density, vocal
intensity, arrangement density, stereo behavior, and hook repetition relative to the selected genre
profile.

### Weak overall result

This conclusion means that the track falls below documented SecondEar thresholds across several
applicable criteria. It must name those criteria and must not be presented as a universal fact about
artistic value.

## Calibration and validation

SecondEar will not train a single opaque model to reproduce review scores. The scoring mechanisms
will use explicit, versioned formulas and will be calibrated manually against evidence and human
consensus.

The initial research process is:

1. Select tracks with sufficient reviews and lawful access to the audio.
2. Record aggregate category scores, review count, score spread, and concrete reviewer arguments.
3. Exclude Atmosphere / Vibe from the target model.
4. Run a fixed SecondEar analyzer and formula version.
5. Compare compatible grouped criteria and inspect the supporting metrics.
6. Change a documented feature, formula, threshold, or genre profile only when the evidence supports
   the change.
7. Increase the relevant analyzer or formula version.
8. Re-evaluate the complete calibration and validation sets.

Tracks receiving 90 points are useful upper anchors but cannot define the complete scale. Calibration
must also include strong, middle, weak, and lower anchors across multiple genres. Separate
calibration, validation, and holdout sets are required even though the formulas are adjusted manually.

Human consensus is a benchmark, not unquestionable ground truth. Review disagreement must be retained
as data rather than averaged away without record.

The review site's four objective-category groups can be compared with SecondEar as follows:

```text
Rhymes + Imagery
    <-> human Rhymes / Imagery consensus

Structure + Rhythm
    <-> human Structure / Rhythm consensus

Artist Performance + Mixing + Sound Production
    <-> human Style Implementation consensus

Individuality + Charisma
    <-> human Individuality / Charisma consensus
```

No automated collection or redistribution of third-party audio or reviews should begin until access,
terms, copyright, and permission are resolved.

## Research order

The current methodological estimate of implementation difficulty is:

1. Mixing
2. Rhymes
3. Rhythm
4. Structure
5. Artist Performance
6. Sound Production
7. Imagery
8. Charisma / Expressive Delivery
9. Individuality

This order is not the delivery roadmap. Early product slices may prioritize architectural learning
over criterion completeness.

## Open methodology decisions

- exact formulas and sub-score weights for every criterion;
- whether scores are continuous internally and how display rounding works;
- how overall scoring behaves when a criterion is unavailable;
- whether the nine criteria have equal weight or their four parent groups have equal weight;
- core genre taxonomy and mixed-genre behavior;
- minimum text, audio, stem, and artist-catalog requirements;
- confidence composition and refusal thresholds;
- corpus construction, licensing, and versioning;
- reviewer-consensus aggregation and disagreement measures;
- calibration, validation, and holdout sample sizes.
