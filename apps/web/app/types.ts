export type LanguageProfile = "en-US" | "en-GB";
export type PrimaryTag = "rap" | "pop" | "rnb" | "rock" | "country" | "electronic";
export type RhymeType = "exact" | "near" | "identity" | "assonance" | "consonance";

export interface SourceSpan {
  line_index: number;
  start: number;
  end: number;
}

export interface PronunciationIssue {
  token_id: string;
  token: string;
  normalized: string;
  span: SourceSpan;
  reason: string;
  choices: string[];
  blocks_score: boolean;
}

export interface AnalyzedLine {
  section_index: number;
  line_index: number;
  span: SourceSpan;
}

export interface RhymeOccurrence {
  id: string;
  text: string;
  normalized_tokens: string[];
  token_ids: string[];
  phonemes: string[];
  rhyme_zone: string[];
  syllable_count: number;
  section_index: number;
  line_index: number;
  span: SourceSpan;
  is_line_ending: boolean;
}

export interface RhymePair {
  id: string;
  left_occurrence_id: string;
  right_occurrence_id: string;
  rhyme_type: RhymeType;
  position: "line_end" | "internal";
  similarity: number;
  nucleus_similarity: number;
  multisyllabic: boolean;
  multiword: boolean;
  same_word: boolean;
  lemma_comparable: boolean;
  same_lemma: boolean;
  homophone: boolean;
}

export interface RhymeFamily {
  label: string;
  occurrence_ids: string[];
  line_indices: number[];
}

export interface RhymeChain {
  id: string;
  family_label: string;
  occurrence_ids: string[];
  line_indices: number[];
}

export interface SectionScheme {
  section_index: number;
  label: string;
  occurrence_count: number;
  pattern: string[];
}

export interface Metric {
  key: string;
  value: string | number | boolean;
  unit: string | null;
  evidence_type: string;
  analyzer: string;
  analyzer_version: string;
}

export interface RhymeResult {
  criterion: "rhymes";
  status: "evaluated" | "needs_pronunciation_review" | "insufficient_data";
  score: number | null;
  scale_max: 10;
  confidence: number;
  language_profile: LanguageProfile;
  primary_tag: PrimaryTag;
  source_reference: string | null;
  versions: Record<string, string>;
  input_summary: {
    total_sections: number;
    unique_sections: number;
    repeated_sections: number;
    total_lines: number;
    unique_lines: number;
    lexical_tokens: number;
    resolved_tokens: number;
    syllables: number;
    line_endings: number;
    resolved_line_endings: number;
    pronunciation_coverage: number;
    line_ending_coverage: number;
  };
  pronunciation_issues: PronunciationIssue[];
  lines: AnalyzedLine[];
  occurrences: RhymeOccurrence[];
  pairs: RhymePair[];
  families: RhymeFamily[];
  chains: RhymeChain[];
  schemes: SectionScheme[];
  metrics: Metric[];
  subscores: Record<string, number>;
  findings: Array<{
    id: string;
    title: string;
    description: string;
    evidence: string[];
    severity: string;
  }>;
  limitations: string[];
}
