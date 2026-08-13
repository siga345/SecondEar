import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { axe } from "jest-axe";
import { afterEach, describe, expect, it, vi } from "vitest";
import Home from "./page";
import type { RhymeResult } from "./types";

const RESULT: RhymeResult = {
  criterion: "rhymes",
  status: "evaluated",
  score: 7.4,
  scale_max: 10,
  confidence: 0.91,
  language_profile: "en-US",
  primary_tag: "pop",
  source_reference: null,
  versions: {
    analysis_version: "rhymes-analysis-0.1.0",
    formula_version: "english-rhymes-score-0.1.0",
    dictionary_sha256: "a".repeat(64),
  },
  input_summary: {
    total_sections: 1,
    unique_sections: 1,
    repeated_sections: 0,
    total_lines: 8,
    unique_lines: 8,
    lexical_tokens: 48,
    resolved_tokens: 48,
    syllables: 60,
    line_endings: 8,
    resolved_line_endings: 8,
    pronunciation_coverage: 1,
    line_ending_coverage: 1,
  },
  pronunciation_issues: [],
  lines: [
    { section_index: 0, line_index: 0, span: { line_index: 0, start: 0, end: 5 } },
    { section_index: 0, line_index: 1, span: { line_index: 1, start: 6, end: 11 } },
  ],
  occurrences: [
    {
      id: "o1",
      text: "night",
      normalized_tokens: ["night"],
      token_ids: ["t1"],
      phonemes: ["n", "ˈaɪ", "t"],
      rhyme_zone: ["ˈaɪ", "t"],
      syllable_count: 1,
      section_index: 0,
      line_index: 0,
      span: { line_index: 0, start: 0, end: 5 },
      is_line_ending: true,
    },
    {
      id: "o2",
      text: "light",
      normalized_tokens: ["light"],
      token_ids: ["t2"],
      phonemes: ["l", "ˈaɪ", "t"],
      rhyme_zone: ["ˈaɪ", "t"],
      syllable_count: 1,
      section_index: 0,
      line_index: 1,
      span: { line_index: 1, start: 6, end: 11 },
      is_line_ending: true,
    },
  ],
  pairs: [
    {
      id: "rp1",
      left_occurrence_id: "o1",
      right_occurrence_id: "o2",
      rhyme_type: "exact",
      position: "line_end",
      similarity: 1,
      nucleus_similarity: 1,
      multisyllabic: false,
      multiword: false,
      same_word: false,
      lemma_comparable: true,
      same_lemma: false,
      homophone: false,
    },
  ],
  families: [{ label: "A", occurrence_ids: ["o1", "o2"], line_indices: [0, 1] }],
  chains: [{ id: "chain-A", family_label: "A", occurrence_ids: ["o1", "o2"], line_indices: [0, 1] }],
  schemes: [{ section_index: 0, label: "Verse", occurrence_count: 1, pattern: ["A", "A"] }],
  metrics: [
    {
      key: "accepted_rhyme_pair_count",
      value: 1,
      unit: "pairs",
      evidence_type: "derived",
      analyzer: "english_rhymes",
      analyzer_version: "0.1.0",
    },
  ],
  subscores: {
    phonetic_strength: 0.8,
    rhyme_density_and_coverage: 0.7,
    construction_complexity: 0.5,
    family_and_lexical_diversity: 0.7,
    scheme_and_section_development: 0.8,
  },
  findings: [],
  limitations: ["Dictionary pronunciation is not performed pronunciation."],
};

afterEach(() => vi.restoreAllMocks());

describe("Rhymes page", () => {
  it("loads a local text file and renders a scored result", async () => {
    const user = userEvent.setup();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => RESULT }),
    );
    const { container } = render(<Home />);
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    await user.upload(fileInput, new File(["one line\nanother line"], "lyrics.txt", { type: "text/plain" }));
    expect(screen.getByRole("textbox", { name: "English lyrics" })).toHaveValue(
      "one line\nanother line",
    );

    await user.click(screen.getByRole("button", { name: "Analyze rhyme construction" }));
    expect(await screen.findByText("7.4")).toBeInTheDocument();
    expect(screen.getByText("Family A")).toBeInTheDocument();
    expect(screen.getAllByText("night").length).toBeGreaterThan(0);
    expect(screen.getByLabelText("Lyrics with highlighted rhyme families")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "internal" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "multisyllabic" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "exact" }));
    expect(screen.queryByText("↔")).not.toBeInTheDocument();
    expect(await axe(container)).toHaveNoViolations();
  });

  it("requires a blocking pronunciation override before re-analysis", async () => {
    const user = userEvent.setup();
    const reviewResult: RhymeResult = {
      ...RESULT,
      status: "needs_pronunciation_review",
      score: null,
      pronunciation_issues: [
        {
          token_id: "s0.l7.t4",
          token: "glorptastic",
          normalized: "glorptastic",
          span: { line_index: 7, start: 10, end: 21 },
          reason: "out_of_vocabulary",
          choices: [],
          blocks_score: true,
        },
      ],
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true, json: async () => reviewResult })
      .mockResolvedValueOnce({ ok: true, json: async () => RESULT });
    vi.stubGlobal("fetch", fetchMock);
    render(<Home />);

    await user.click(screen.getByRole("button", { name: "Load an example" }));
    await user.click(screen.getByRole("button", { name: "Analyze rhyme construction" }));
    const rerun = await screen.findByRole("button", { name: "Re-run with reviewed pronunciations" });
    expect(rerun).toBeDisabled();

    await user.type(screen.getByRole("textbox", { name: "Pronunciation for glorptastic" }), "G L AO1 R P");
    expect(rerun).toBeEnabled();
    await user.click(rerun);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    const secondPayload = JSON.parse(fetchMock.mock.calls[1][1].body as string);
    expect(secondPayload.pronunciation_overrides).toEqual([
      { target: "s0.l7.t4", pronunciation: "G L AO1 R P" },
    ]);
  });
});
