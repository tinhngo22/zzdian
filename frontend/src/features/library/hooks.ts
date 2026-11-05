import { useCallback } from "react";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
  type QueryClient,
} from "@tanstack/react-query";
import { isApiError } from "../../api/client";
import {
  addSetWord,
  addSetWords,
  createSet,
  deleteSet,
  getWordCharacters,
  getWordsByCharacter,
  getWordsByComponent,
  listSets,
  listSetWords,
  lookupDictionaryWord,
  removeSetWord,
  renameSet,
} from "../../api/endpoints";
import { queryKeys } from "../../api/queryKeys";
import type { FlashcardSetSummary, NewSetWord } from "../../types/api";

/** Backend default is 200, max 1000. */
export const WORDS_PAGE_SIZE = 200;

/** GET /explore/characters accepts at most 50 character ids. */
export const EXPLORE_MAX_CHARACTERS = 50;

/** Unique code points of a word, in first-appearance order (= characters.id values). */
export function wordCharacterIds(word: string): number[] {
  return [...new Set(Array.from(word, (ch) => ch.codePointAt(0)!))];
}

function invalidateSetList(queryClient: QueryClient) {
  return queryClient.invalidateQueries({ queryKey: queryKeys.sets, exact: true });
}

function invalidateRelatedWords(queryClient: QueryClient) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: queryKeys.wordsByCharacterAll }),
    queryClient.invalidateQueries({ queryKey: queryKeys.wordsByComponentAll }),
  ]);
}

function invalidateSetContents(queryClient: QueryClient, setId: string) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: queryKeys.setWords(setId) }),
    invalidateSetList(queryClient),
    invalidateRelatedWords(queryClient),
  ]);
}

// ---------- queries ----------

export function useSets() {
  return useQuery({ queryKey: queryKeys.sets, queryFn: listSets });
}

export function useSetWords(setId: string, enabled = true) {
  return useInfiniteQuery({
    queryKey: queryKeys.setWords(setId),
    queryFn: ({ pageParam }) => listSetWords(setId, WORDS_PAGE_SIZE, pageParam),
    initialPageParam: 0,
    getNextPageParam: (lastPage, pages) => {
      const loaded = pages.reduce((sum, page) => sum + page.items.length, 0);
      if (lastPage.items.length === 0 || loaded >= lastPage.total) return undefined;
      return loaded;
    },
    enabled,
  });
}

export function useWordCharacters(word: string) {
  const ids = wordCharacterIds(word);
  return useQuery({
    queryKey: queryKeys.wordCharacters(word),
    queryFn: () => getWordCharacters(ids),
    enabled: ids.length > 0 && ids.length <= EXPLORE_MAX_CHARACTERS,
    staleTime: 60 * 60 * 1000,
  });
}

/** On-demand dictionary lookup (cached), for autofilling a word the user just typed. */
export function useDictionaryLookup() {
  const queryClient = useQueryClient();
  return useCallback(
    (simplified: string) =>
      queryClient.fetchQuery({
        queryKey: queryKeys.dictionaryWord(simplified),
        queryFn: () => lookupDictionaryWord(simplified),
        staleTime: 60 * 60 * 1000,
      }),
    [queryClient],
  );
}

export function useWordsByCharacter(characterId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.wordsByCharacter(characterId),
    queryFn: () => getWordsByCharacter(characterId),
    enabled,
  });
}

export function useWordsByComponent(componentId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.wordsByComponent(componentId),
    queryFn: () => getWordsByComponent(componentId),
    enabled,
  });
}

// ---------- set mutations ----------

export function useCreateSet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => createSet(name),
    onSuccess: () => invalidateSetList(queryClient),
  });
}

export function useRenameSet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ setId, name }: { setId: string; name: string }) => renameSet(setId, name),
    onSuccess: (updated) => {
      queryClient.setQueryData<FlashcardSetSummary[]>(queryKeys.sets, (sets) =>
        sets?.map((s) => (s.id === updated.id ? { ...s, name: updated.name } : s)),
      );
      return invalidateSetList(queryClient);
    },
    onError: (error) => {
      if (isApiError(error, 404)) void invalidateSetList(queryClient);
    },
  });
}

export function useDeleteSet({ onDeleted }: { onDeleted?: () => void } = {}) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (setId: string) => deleteSet(setId),
    onSuccess: (_data, setId) => {
      onDeleted?.();
      queryClient.removeQueries({ queryKey: queryKeys.setWords(setId) });
      queryClient.setQueryData<FlashcardSetSummary[]>(queryKeys.sets, (sets) =>
        sets?.filter((s) => s.id !== setId),
      );
      return Promise.all([invalidateSetList(queryClient), invalidateRelatedWords(queryClient)]);
    },
    onError: (error) => {
      if (isApiError(error, 404)) void invalidateSetList(queryClient);
    },
  });
}

// ---------- word mutations ----------

export function useAddWord(setId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (word: NewSetWord) => addSetWord(setId, word),
    onSuccess: () => invalidateSetContents(queryClient, setId),
    onError: (error) => {
      if (isApiError(error, 404)) void invalidateSetList(queryClient);
    },
  });
}

export function useAddWords(setId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (words: NewSetWord[]) => addSetWords(setId, words),
    onSuccess: () => invalidateSetContents(queryClient, setId),
    onError: (error) => {
      if (isApiError(error, 404)) void invalidateSetList(queryClient);
    },
  });
}

export function useRemoveWord(setId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (wordId: string) => removeSetWord(setId, wordId),
    onSuccess: () => invalidateSetContents(queryClient, setId),
    onError: (error) => {
      if (isApiError(error, 404)) void invalidateSetContents(queryClient, setId);
    },
  });
}
