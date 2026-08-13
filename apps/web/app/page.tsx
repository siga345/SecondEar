"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";
import type {
  LanguageProfile,
  PrimaryTag,
  PronunciationIssue,
  RhymeOccurrence,
  RhymeResult,
  RhymeType,
} from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
const MAX_FILE_BYTES = 256 * 1024;
const GENRES: Array<{ value: PrimaryTag; label: string }> = [
  { value: "rap", label: "Rap" },
  { value: "pop", label: "Pop" },
  { value: "rnb", label: "R&B" },
  { value: "rock", label: "Rock" },
  { value: "country", label: "Country" },
  { value: "electronic", label: "Electronic" },
];
type RelationFilter = RhymeType | "internal" | "multisyllabic";

const FILTERS: RelationFilter[] = [
  "exact",
  "near",
  "identity",
  "internal",
  "multisyllabic",
  "assonance",
  "consonance",
];
const FAMILY_STYLES = ["family-one", "family-two", "family-three", "family-four", "family-five"];

const SAMPLE = `[Verse]
I carry every story and follow the light
I answer every warning and travel at night
I gather all the pieces and make the words bright
I measure every cadence until it is right

[Chorus]
We stand beside the river with maps in our hand
We plan another passage across the open land
We mark another measure exactly as planned
We start another chapter and build where we stand`;

type Overrides = Record<string, string>;
type FamilyPresentation = { label: string; style: string };

interface DisplayLine {
  lineIndex: number;
  start: number;
  text: string;
}

function formatKey(value: string) {
  return value.replaceAll("_", " ");
}

function EvidenceLine({
  line,
  occurrences,
  familyByOccurrence,
  schemeLabel,
}: {
  line: DisplayLine;
  occurrences: RhymeOccurrence[];
  familyByOccurrence: Map<string, FamilyPresentation>;
  schemeLabel: string;
}) {
  const longestByFamily = new Map<string, { occurrence: RhymeOccurrence; family: FamilyPresentation }>();
  occurrences.forEach((occurrence) => {
    const family = familyByOccurrence.get(occurrence.id);
    if (!family) return;
    const previous = longestByFamily.get(family.label);
    if (!previous || occurrence.span.end - occurrence.span.start > previous.occurrence.span.end - previous.occurrence.span.start) {
      longestByFamily.set(family.label, { occurrence, family });
    }
  });
  const highlights = [...longestByFamily.values()]
    .map((value) => ({
      ...value,
      start: Math.max(0, value.occurrence.span.start - line.start),
      end: Math.min(line.text.length, value.occurrence.span.end - line.start),
    }))
    .filter((value) => value.end > value.start)
    .sort((left, right) => left.start - right.start);
  const content: React.ReactNode[] = [];
  let cursor = 0;
  highlights.forEach((highlight) => {
    if (highlight.start < cursor) return;
    content.push(line.text.slice(cursor, highlight.start));
    content.push(
      <mark
        className={highlight.family.style}
        title={`Rhyme family ${highlight.family.label}`}
        key={`${highlight.family.label}-${highlight.start}`}
      >
        <span className="sr-only">Rhyme family {highlight.family.label}: </span>
        {line.text.slice(highlight.start, highlight.end)}
        <sup aria-hidden="true">{highlight.family.label}</sup>
      </mark>,
    );
    cursor = highlight.end;
  });
  content.push(line.text.slice(cursor));
  return (
    <div className="evidence-line">
      <span className="line-number">{String(line.lineIndex + 1).padStart(2, "0")}</span>
      <span>{content}</span>
      <span className="scheme-letter" aria-label={`Scheme label ${schemeLabel}`}>{schemeLabel}</span>
    </div>
  );
}

function ReviewIssue({
  issue,
  value,
  profile,
  onChange,
}: {
  issue: PronunciationIssue;
  value: string;
  profile: LanguageProfile;
  onChange: (value: string) => void;
}) {
  return (
    <div className={`review-row ${issue.blocks_score ? "blocking" : ""}`}>
      <div>
        <strong>{issue.token}</strong>
        <span className="token-id">line {issue.span.line_index + 1}</span>
      </div>
      <label>
        <span className="sr-only">Pronunciation for {issue.token}</span>
        {issue.choices.length ? (
          <select value={value} onChange={(event) => onChange(event.target.value)}>
            <option value="">Select pronunciation</option>
            {issue.choices.map((choice) => (
              <option value={choice} key={choice}>
                {choice}
              </option>
            ))}
          </select>
        ) : (
          <input
            value={value}
            onChange={(event) => onChange(event.target.value)}
            placeholder={profile === "en-US" ? "ARPAbet: N AY1 T" : "IPA: n ˈaɪ t"}
          />
        )}
      </label>
      <span className="review-reason">
        {formatKey(issue.reason)} {issue.blocks_score ? "· required" : "· optional"}
      </span>
    </div>
  );
}

export default function Home() {
  const [lyrics, setLyrics] = useState("");
  const [profile, setProfile] = useState<LanguageProfile>("en-US");
  const [genre, setGenre] = useState<PrimaryTag>("pop");
  const [sourceReference, setSourceReference] = useState("");
  const [overrides, setOverrides] = useState<Overrides>({});
  const [result, setResult] = useState<RhymeResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [filters, setFilters] = useState<Set<RelationFilter>>(new Set(FILTERS));

  const occurrenceById = useMemo(
    () => new Map(result?.occurrences.map((occurrence) => [occurrence.id, occurrence]) ?? []),
    [result],
  );
  const familyByOccurrence = useMemo(() => {
    const values = new Map<string, FamilyPresentation>();
    result?.families.forEach((family, index) => {
      family.occurrence_ids.forEach((id) =>
        values.set(id, { label: family.label, style: FAMILY_STYLES[index % FAMILY_STYLES.length] }),
      );
    });
    return values;
  }, [result]);
  const visiblePairs = result?.pairs.filter(
    (pair) =>
      filters.has(pair.rhyme_type) &&
      (pair.position !== "internal" || filters.has("internal")) &&
      (!pair.multisyllabic || filters.has("multisyllabic")),
  ) ?? [];
  const displayLines = useMemo(
    () =>
      result?.lines.map((line) => ({
        lineIndex: line.line_index,
        start: line.span.start,
        text: lyrics.slice(line.span.start, line.span.end),
      })) ?? [],
    [lyrics, result],
  );
  const occurrencesByLine = useMemo(() => {
    const values = new Map<number, RhymeOccurrence[]>();
    result?.occurrences.forEach((occurrence) => {
      const current = values.get(occurrence.line_index) ?? [];
      current.push(occurrence);
      values.set(occurrence.line_index, current);
    });
    return values;
  }, [result]);
  const schemeByLine = useMemo(() => {
    const values = new Map<number, string>();
    let lineIndex = 0;
    result?.schemes.forEach((scheme) => {
      scheme.pattern.forEach((label) => {
        values.set(lineIndex, label);
        lineIndex += 1;
      });
    });
    return values;
  }, [result]);

  async function analyze(event?: FormEvent) {
    event?.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/v1/rhymes/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lyrics,
          language_profile: profile,
          primary_tag: genre,
          source_reference: sourceReference || null,
          pronunciation_overrides: Object.entries(overrides)
            .filter(([, pronunciation]) => pronunciation.trim())
            .map(([target, pronunciation]) => ({ target, pronunciation: pronunciation.trim() })),
        }),
      });
      if (!response.ok) {
        const payload = (await response.json()) as { detail?: string | Array<{ msg: string }> };
        const detail = Array.isArray(payload.detail)
          ? payload.detail.map((item) => item.msg).join("; ")
          : payload.detail;
        throw new Error(detail ?? "The analysis request was rejected.");
      }
      setResult((await response.json()) as RhymeResult);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to analyze the lyrics.");
    } finally {
      setLoading(false);
    }
  }

  async function readFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (!/\.(txt|md)$/i.test(file.name)) {
      setError("Choose a UTF-8 .txt or .md file.");
      return;
    }
    if (file.size > MAX_FILE_BYTES) {
      setError("The lyrics file exceeds the 256 KiB limit.");
      return;
    }
    try {
      const decoded = new TextDecoder("utf-8", { fatal: true }).decode(await file.arrayBuffer());
      setLyrics(decoded);
    } catch {
      setError("Choose a valid UTF-8 .txt or .md file.");
      return;
    }
    setOverrides({});
    setResult(null);
    setError("");
  }

  function toggleFilter(filter: RelationFilter) {
    setFilters((current) => {
      const next = new Set(current);
      if (next.has(filter)) next.delete(filter);
      else next.add(filter);
      return next;
    });
  }

  const requiredIssues = result?.pronunciation_issues.filter((issue) => issue.blocks_score) ?? [];
  const reviewComplete = requiredIssues.every((issue) => overrides[issue.token_id]?.trim());
  const hasReviewOverrides = Object.values(overrides).some((value) => value.trim());

  return (
    <main>
      <header className="masthead">
        <a className="brand" href="#top" aria-label="SecondEar home">
          <span className="brand-mark">SE</span>
          <span>SecondEar</span>
        </a>
        <div className="method-tag">Rhymes / formula 0.1</div>
      </header>

      <section className="hero" id="top">
        <div>
          <p className="eyebrow">Phonetic construction, measured</p>
          <h1>See the rhyme system hiding in your lyrics.</h1>
        </div>
        <p className="hero-copy">
          No taste. No attachment. Just traceable phonemes, families, schemes, and a
          genre-relative criterion score.
        </p>
      </section>

      <form className="input-panel" onSubmit={analyze}>
        <div className="panel-heading">
          <div>
            <span className="step">01</span>
            <h2>Submit lyrics</h2>
          </div>
          <label className="file-action">
            Upload .txt or .md
            <input type="file" accept=".txt,.md,text/plain,text/markdown" onChange={readFile} />
          </label>
        </div>

        <label className="lyrics-field">
          <span className="sr-only">English lyrics</span>
          <textarea
            value={lyrics}
            onChange={(event) => {
              setLyrics(event.target.value);
              setResult(null);
              setOverrides({});
            }}
            placeholder="Paste line-broken English lyrics. Section labels such as [Verse] and [Chorus] are supported."
            maxLength={262_144}
            required
          />
        </label>

        <div className="control-grid">
          <label>
            <span>Pronunciation profile</span>
            <select
              value={profile}
              onChange={(event) => {
                setProfile(event.target.value as LanguageProfile);
                setOverrides({});
                setResult(null);
              }}
            >
              <option value="en-US">English — United States</option>
              <option value="en-GB">English — Great Britain (SSB/RP)</option>
            </select>
          </label>
          <label>
            <span>Primary tag</span>
            <select
              value={genre}
              onChange={(event) => {
                setGenre(event.target.value as PrimaryTag);
                setResult(null);
              }}
            >
              {GENRES.map((item) => (
                <option value={item.value} key={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Source reference <small>optional</small></span>
            <input
              type="url"
              value={sourceReference}
              onChange={(event) => {
                setSourceReference(event.target.value);
                setResult(null);
              }}
              placeholder="https://genius.com/..."
            />
          </label>
        </div>

        <div className="submit-row">
          <button
            type="button"
            className="text-button"
            onClick={() => {
              setLyrics(SAMPLE);
              setOverrides({});
              setResult(null);
            }}
          >
            Load an example
          </button>
          <button className="primary-button" type="submit" disabled={loading || !lyrics.trim()}>
            {loading ? "Analyzing…" : "Analyze rhyme construction"}
          </button>
        </div>
        <p className="privacy-note">Lyrics are analyzed synchronously and are not retained.</p>
        {error && <p className="error-message" role="alert">{error}</p>}
      </form>

      {result && (
        <div className="results" aria-live="polite">
          {!!result.pronunciation_issues.length && (
            <section className="review-panel">
              <div className="panel-heading">
                <div>
                  <span className="step">02</span>
                  <h2>Review pronunciation</h2>
                </div>
                <span className="status-badge">
                  {requiredIssues.length ? `${requiredIssues.length} required` : "optional review"}
                </span>
              </div>
              <p className="section-intro">
                {requiredIssues.length
                  ? "The selected dictionary cannot defend every line ending."
                  : "Some internal tokens are ambiguous or outside the selected dictionary."}{" "}
                Choose a listed pronunciation or enter one in {profile === "en-US" ? "ARPAbet" : "IPA"}.
              </p>
              <div className="review-list">
                {result.pronunciation_issues.map((issue) => (
                  <ReviewIssue
                    key={issue.token_id}
                    issue={issue}
                    value={overrides[issue.token_id] ?? ""}
                    profile={profile}
                    onChange={(value) => setOverrides((current) => ({ ...current, [issue.token_id]: value }))}
                  />
                ))}
              </div>
              <button
                className="primary-button"
                onClick={() => analyze()}
                disabled={!reviewComplete || !hasReviewOverrides || loading}
              >
                Re-run with reviewed pronunciations
              </button>
            </section>
          )}

          <section className="score-panel">
            <div className="score-block">
              <span className="step">03</span>
              <p>Rhymes</p>
              <strong>{result.score ?? "—"}<small>/10</small></strong>
              <span className={`result-status ${result.status}`}>{formatKey(result.status)}</span>
            </div>
            <div className="confidence-block">
              <div className="confidence-label">
                <span>Confidence</span>
                <strong>{Math.round(result.confidence * 100)}%</strong>
              </div>
              <div
                className="meter"
                role="progressbar"
                aria-label="Analysis confidence"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(result.confidence * 100)}
              >
                <span style={{ width: `${result.confidence * 100}%` }} />
              </div>
              <dl className="summary-grid">
                <div><dt>Unique lines</dt><dd>{result.input_summary.unique_lines}</dd></div>
                <div><dt>Pronunciation</dt><dd>{Math.round(result.input_summary.pronunciation_coverage * 100)}%</dd></div>
                <div><dt>Rhyme pairs</dt><dd>{result.metrics.find((metric) => metric.key === "accepted_rhyme_pair_count")?.value ?? 0}</dd></div>
                <div><dt>Repeated sections</dt><dd>{result.input_summary.repeated_sections}</dd></div>
              </dl>
            </div>
          </section>

          <section className="evidence-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Traceable evidence</p>
                <h2>Rhyme families</h2>
              </div>
              <div className="scheme-list">
                {result.schemes.map((scheme) => (
                  <span key={scheme.section_index}>
                    {scheme.label}: <strong>{scheme.pattern.join(" ")}</strong>
                    {scheme.occurrence_count > 1 ? ` ×${scheme.occurrence_count}` : ""}
                  </span>
                ))}
              </div>
            </div>
            <div className="lyrics-evidence" aria-label="Lyrics with highlighted rhyme families">
              {displayLines.map((line) => (
                <EvidenceLine
                  line={line}
                  occurrences={occurrencesByLine.get(line.lineIndex) ?? []}
                  familyByOccurrence={familyByOccurrence}
                  schemeLabel={schemeByLine.get(line.lineIndex) ?? "X"}
                  key={line.lineIndex}
                />
              ))}
            </div>
            <div className="family-grid">
              {result.families.map((family, index) => (
                <article className={`family-card ${FAMILY_STYLES[index % FAMILY_STYLES.length]}`} key={family.label}>
                  <span className="family-label">Family {family.label}</span>
                  <div>
                    {family.occurrence_ids.map((id) => {
                      const occurrence = occurrenceById.get(id);
                      return occurrence ? (
                        <span className="family-word" key={id}>
                          {occurrence.text}<small>/{occurrence.rhyme_zone.join(" ")}/</small>
                        </span>
                      ) : null;
                    })}
                  </div>
                </article>
              ))}
              {!result.families.length && <p className="empty-state">No line-ending family passed the scoring threshold.</p>}
            </div>
          </section>

          <section className="pairs-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Pair evidence</p>
                <h2>Detected relationships</h2>
              </div>
              <div className="filter-list" aria-label="Filter rhyme relations">
                {FILTERS.map((filter) => (
                  <button
                    className={filters.has(filter) ? "active" : ""}
                    type="button"
                    aria-pressed={filters.has(filter)}
                    onClick={() => toggleFilter(filter)}
                    key={filter}
                  >
                    {filter}
                  </button>
                ))}
              </div>
            </div>
            <div className="pair-list">
              {visiblePairs.map((pair) => {
                const left = occurrenceById.get(pair.left_occurrence_id);
                const right = occurrenceById.get(pair.right_occurrence_id);
                const family = familyByOccurrence.get(pair.left_occurrence_id);
                return (
                  <article className="pair-row" key={pair.id}>
                    <span className={`relation-type ${family?.style ?? ""}`}>{family?.label ?? pair.rhyme_type.slice(0, 1).toUpperCase()}</span>
                    <div className="pair-words">
                      <strong>{left?.text}</strong><span>↔</span><strong>{right?.text}</strong>
                    </div>
                    <div className="pair-tags">
                      <span>{pair.rhyme_type}</span><span>{formatKey(pair.position)}</span>
                      {pair.multisyllabic && <span>multisyllabic</span>}
                      {pair.multiword && <span>multiword</span>}
                    </div>
                    <strong className="similarity">{Math.round(pair.similarity * 100)}%</strong>
                  </article>
                );
              })}
            </div>
          </section>

          <section className="detail-grid">
            <article>
              <p className="eyebrow">Formula components</p>
              <h2>Profile-relative construction</h2>
              <div className="component-list">
                {Object.entries(result.subscores).map(([key, value]) => (
                  <div key={key}>
                    <span>{formatKey(key)}</span><strong>{Math.round(value * 100)}</strong>
                    <div className="mini-meter"><span style={{ width: `${value * 100}%` }} /></div>
                  </div>
                ))}
              </div>
            </article>
            <article>
              <p className="eyebrow">Metric ledger</p>
              <h2>Measured and derived</h2>
              <table>
                <tbody>
                  {result.metrics.map((metric) => (
                    <tr key={metric.key}>
                      <th>{formatKey(metric.key)}</th>
                      <td>{String(metric.value)}{metric.unit ? ` ${metric.unit}` : ""}</td>
                      <td>{metric.evidence_type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </article>
          </section>

          {!!result.findings.length && (
            <section className="findings-panel">
              <p className="eyebrow">Evidence-backed findings</p>
              <div className="finding-list">
                {result.findings.map((finding) => (
                  <article key={finding.id}>
                    <span>{finding.severity}</span>
                    <h2>{finding.title}</h2>
                    <p>{finding.description}</p>
                    <small>Evidence: {finding.evidence.map(formatKey).join(", ")}</small>
                  </article>
                ))}
              </div>
            </section>
          )}

          <section className="method-panel">
            <details>
              <summary>Versions and limitations</summary>
              <div className="method-content">
                <dl>
                  {Object.entries(result.versions).map(([key, value]) => (
                    <div key={key}><dt>{formatKey(key)}</dt><dd>{value}</dd></div>
                  ))}
                </dl>
                <ul>{result.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
              </div>
            </details>
          </section>
        </div>
      )}
    </main>
  );
}
