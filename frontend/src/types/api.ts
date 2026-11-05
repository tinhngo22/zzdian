// Shapes mirror the backend responses documented in data/README.md.
// UUIDs and timestamps arrive as JSON strings.

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
}

export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface FlashcardSet {
  id: string;
  name: string;
  created_at: string;
}

export interface FlashcardSetSummary extends FlashcardSet {
  word_count: number;
}

export interface SetWord {
  id: string;
  simplified: string;
  traditional: string | null;
  pinyin: string | null;
  definitions: string | null;
  added_at: string;
}

export interface SetWordsPage {
  total: number;
  items: SetWord[];
}

export interface NewSetWord {
  simplified: string;
  traditional?: string;
  pinyin?: string;
  definitions?: string;
}

export interface AddSetWordsResponse {
  items: SetWord[];
}

/** A reference dictionary (CC-CEDICT) entry. */
export interface DictionaryWord {
  id: number;
  simplified: string;
  traditional: string;
  /** Tone marks: "nǐ hǎo". */
  pinyin: string;
  definitions: string[];
}

export interface DictionaryLookupResponse {
  simplified: string;
  /** Common words first, then proper nouns; empty if the word is not in the dictionary. */
  entries: DictionaryWord[];
}

export interface CharacterComponent {
  position: number;
  role: "component" | "semantic" | "phonetic" | string;
  id: number;
  glyph: string;
  pinyin: string[] | null;
  meaning_en: string | null;
}

export interface ExploreCharacter {
  id: number;
  glyph: string;
  pinyin: string[] | null;
  meaning_en: string | null;
  stroke_count: number | null;
  main_radical_id: number | null;
  /** Empty for characters that do not decompose (人, 女, ...). */
  components: CharacterComponent[];
}

export interface WordCharacterEntry {
  id: number;
  glyph: string;
  is_hanzi: boolean;
  character: ExploreCharacter | null;
}

export interface WordCharactersResponse {
  character_ids: number[];
  characters: WordCharacterEntry[];
}

export interface WordsByCharacterResponse {
  character_id: number;
  words: SetWord[];
}

export interface WordsByComponentResponse {
  component_id: number;
  words: SetWord[];
}
