import { isApiError } from "../../api/client";

export const SET_NAME_MAX_LENGTH = 100;

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function isUuid(value: string | undefined): value is string {
  return !!value && UUID_RE.test(value);
}

export function pluralizeWords(count: number) {
  return `${count} ${count === 1 ? "word" : "words"}`;
}

export function formatDate(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

/** Returns an error message, or null if the trimmed name is valid. */
export function validateSetName(name: string): string | null {
  const trimmed = name.trim();
  if (!trimmed) return "Enter a name for the set.";
  if (trimmed.length > SET_NAME_MAX_LENGTH) {
    return `Keep the name under ${SET_NAME_MAX_LENGTH} characters (currently ${trimmed.length}).`;
  }
  return null;
}

const KANGXI_RADICALS_START = 0x2f00;
const KANGXI_RADICAL_COUNT = 214;

/** Everyday glyph of Kangxi radical `n` (1–214), e.g. 38 → 女. */
export function kangxiRadicalGlyph(n: number): string | null {
  if (!Number.isInteger(n) || n < 1 || n > KANGXI_RADICAL_COUNT) return null;
  // The Kangxi Radicals block (⼥) NFKC-normalizes to the ordinary character (女).
  return String.fromCodePoint(KANGXI_RADICALS_START + n - 1).normalize("NFKC");
}

export function errorMessage(error: unknown, notFoundMessage = "Set not found."): string {
  if (isApiError(error, 404)) return notFoundMessage;
  if (isApiError(error)) return error.message;
  return "Something went wrong. Please try again.";
}
