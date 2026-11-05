import type { NewSetWord } from "../../types/api";

/** POST /sets/{id}/words/bulk accepts at most 500 words. */
export const MAX_IMPORT_WORDS = 500;

export type ImportField = "simplified" | "traditional" | "pinyin" | "definitions";

export const FIELD_LABELS: Record<ImportField, string> = {
  simplified: "Simplified",
  traditional: "Traditional",
  pinyin: "Pinyin",
  definitions: "Definitions",
};

export const COLUMN_LAYOUTS = {
  spd: ["simplified", "pinyin", "definitions"],
  sd: ["simplified", "definitions"],
  stpd: ["simplified", "traditional", "pinyin", "definitions"],
} satisfies Record<string, ImportField[]>;

export type ColumnLayout = keyof typeof COLUMN_LAYOUTS;

export const FIELD_SEPARATORS = { tab: "\t", comma: "," } as const;
export const ROW_SEPARATORS = { newline: "\n", semicolon: ";" } as const;

export interface ImportOptions {
  /** Between the fields of one word. */
  fieldSeparator: string;
  /** Between words. */
  rowSeparator: string;
  layout: ColumnLayout;
}

export type ParsedRow =
  | { row: number; word: NewSetWord; error?: undefined }
  | { row: number; word?: undefined; error: string; raw: string };

/**
 * Quizlet-style import: one word per row, fields in `layout` order. Blank rows are
 * ignored. Extra fields are joined back into the last column, so a definition may
 * itself contain the field separator ("good, well" with comma-separated fields).
 */
export function parseImport(text: string, { fieldSeparator, rowSeparator, layout }: ImportOptions): ParsedRow[] {
  if (!fieldSeparator || !rowSeparator) return [];
  const fields = COLUMN_LAYOUTS[layout];
  const rows = text.replace(/\r\n?/g, "\n").split(rowSeparator);
  const parsed: ParsedRow[] = [];

  rows.forEach((raw, index) => {
    if (!raw.trim()) return;
    const parts = raw.split(fieldSeparator);
    const values = [
      ...parts.slice(0, fields.length - 1),
      parts.slice(fields.length - 1).join(fieldSeparator),
    ].map((v) => v?.trim() ?? "");

    const word: Partial<NewSetWord> = {};
    fields.forEach((field, i) => {
      if (values[i]) word[field] = values[i];
    });
    if (!word.simplified) {
      parsed.push({ row: index + 1, error: "Missing the Chinese word", raw: raw.trim() });
      return;
    }
    parsed.push({ row: index + 1, word: word as NewSetWord });
  });
  return parsed;
}
