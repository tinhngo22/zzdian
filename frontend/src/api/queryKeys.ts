export const queryKeys = {
  me: ["me"] as const,
  sets: ["sets"] as const,
  setWords: (setId: string) => ["sets", setId, "words"] as const,
  dictionaryWord: (simplified: string) => ["dictionary", "words", simplified] as const,
  wordCharacters: (word: string) => ["explore", "characters", word] as const,
  wordsByCharacterAll: ["explore", "words-by-character"] as const,
  wordsByCharacter: (characterId: number) =>
    ["explore", "words-by-character", characterId] as const,
  wordsByComponentAll: ["explore", "words-by-component"] as const,
  wordsByComponent: (componentId: number) =>
    ["explore", "words-by-component", componentId] as const,
};
