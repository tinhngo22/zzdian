import type {
  AddSetWordsResponse,
  DictionaryLookupResponse,
  FlashcardSet,
  FlashcardSetSummary,
  NewSetWord,
  SetWord,
  SetWordsPage,
  TokenResponse,
  User,
  WordCharactersResponse,
  WordsByCharacterResponse,
  WordsByComponentResponse,
} from "../types/api";
import { apiRequest } from "./client";

// ---------- auth ----------

export const login = (email: string, password: string) =>
  apiRequest<TokenResponse>("/auth/login", {
    method: "POST",
    body: { email, password },
    auth: false,
  });

export const getMe = () => apiRequest<User>("/auth/me");

// ---------- sets ----------

export const listSets = () => apiRequest<FlashcardSetSummary[]>("/sets");

export const createSet = (name: string) =>
  apiRequest<FlashcardSet>("/sets", { method: "POST", body: { name } });

export const renameSet = (setId: string, name: string) =>
  apiRequest<FlashcardSet>(`/sets/${setId}`, { method: "PATCH", body: { name } });

export const deleteSet = (setId: string) =>
  apiRequest<void>(`/sets/${setId}`, { method: "DELETE" });

export const listSetWords = (setId: string, limit: number, offset: number) =>
  apiRequest<SetWordsPage>(`/sets/${setId}/words`, { query: { limit, offset } });

export const addSetWord = (setId: string, word: NewSetWord) =>
  apiRequest<SetWord>(`/sets/${setId}/words`, { method: "POST", body: word });

/** All or nothing; at most `MAX_BULK_WORDS` (500) words per request. */
export const addSetWords = (setId: string, words: NewSetWord[]) =>
  apiRequest<AddSetWordsResponse>(`/sets/${setId}/words/bulk`, {
    method: "POST",
    body: { words },
  });

export const removeSetWord = (setId: string, wordId: string) =>
  apiRequest<void>(`/sets/${setId}/words/${wordId}`, { method: "DELETE" });

// ---------- dictionary ----------

export const lookupDictionaryWord = (simplified: string) =>
  apiRequest<DictionaryLookupResponse>("/words", { query: { simplified } });

// ---------- explore ----------

/** `characterIds` are the Unicode code points of the word's characters, in order. */
export const getWordCharacters = (characterIds: number[]) =>
  apiRequest<WordCharactersResponse>("/explore/characters", {
    query: { character_id: characterIds },
  });

export const getWordsByCharacter = (characterId: number) =>
  apiRequest<WordsByCharacterResponse>("/explore/words/by-character", {
    query: { character_id: characterId },
  });

export const getWordsByComponent = (componentId: number) =>
  apiRequest<WordsByComponentResponse>("/explore/words/by-component", {
    query: { component_id: componentId },
  });
