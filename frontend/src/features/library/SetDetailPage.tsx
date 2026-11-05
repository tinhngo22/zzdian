import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router";
import { isApiError } from "../../api/client";
import { Button } from "../../components/Button";
import { Dialog } from "../../components/Dialog";
import { Skeleton } from "../../components/Spinner";
import { EmptyState, ErrorState } from "../../components/States";
import { AddWordDialog } from "./AddWordDialog";
import { DeleteSetDialog } from "./DeleteSetDialog";
import { errorMessage, isUuid, pluralizeWords } from "./format";
import { ImportWordsDialog } from "./ImportWordsDialog";
import { useSets, useSetWords } from "./hooks";
import { RenameSetDialog } from "./SetNameDialog";
import { WordModal } from "./WordModal";
import { WordTile, WordTileSkeleton } from "./WordTile";

const GRID =
  "grid grid-cols-6 gap-4 max-lg:grid-cols-4 max-md:grid-cols-3 max-md:gap-3 max-sm:grid-cols-2";

const WORD_PARAM = "word";

export function SetDetailPage() {
  const { setId = "" } = useParams();
  const validId = isUuid(setId);
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [dialog, setDialog] = useState<"add" | "import" | "rename" | "delete" | null>(null);

  const setsQuery = useSets();
  const wordsQuery = useSetWords(setId, validId);

  const set = setsQuery.data?.find((s) => s.id === setId);
  const words = useMemo(
    () => wordsQuery.data?.pages.flatMap((page) => page.items) ?? [],
    [wordsQuery.data],
  );
  const total = wordsQuery.data?.pages.at(-1)?.total ?? 0;

  // ----- word modal state lives in ?word=<id> -----
  const selectedWordId = searchParams.get(WORD_PARAM);
  const selectedWord = selectedWordId ? words.find((w) => w.id === selectedWordId) : undefined;
  const { hasNextPage, isFetchingNextPage, fetchNextPage } = wordsQuery;
  const searchingForWord = !!selectedWordId && !selectedWord && hasNextPage;

  // A deep-linked word may be on a page that is not loaded yet.
  useEffect(() => {
    if (searchingForWord && !isFetchingNextPage) void fetchNextPage();
  }, [searchingForWord, isFetchingNextPage, fetchNextPage]);

  const openWord = (wordId: string) => {
    const next = new URLSearchParams(searchParams);
    next.set(WORD_PARAM, wordId);
    setSearchParams(next, { state: { wordModalPushed: true } });
  };

  const closeWord = () => {
    if ((location.state as { wordModalPushed?: boolean } | null)?.wordModalPushed) {
      navigate(-1);
      return;
    }
    const next = new URLSearchParams(searchParams);
    next.delete(WORD_PARAM);
    setSearchParams(next, { replace: true });
  };

  // There is no GET /sets/{id}, so the set's name and existence come from the set list.
  const setNotFound =
    !validId ||
    isApiError(wordsQuery.error, 404) ||
    isApiError(wordsQuery.error, 422) ||
    (setsQuery.isSuccess && !setsQuery.isFetching && !set);

  if (setNotFound) {
    return (
      <div className="flex flex-col gap-6">
        <BackLink />
        <EmptyState
          title="Set not found"
          description="This set doesn't exist or has been deleted."
          action={
            <Link
              to="/library"
              className="text-sm font-medium text-red-800 underline-offset-2 hover:underline"
            >
              Go to your library
            </Link>
          }
        />
      </div>
    );
  }

  const addWordButton = <Button onClick={() => setDialog("add")}>Add word</Button>;
  const importButton = (
    <Button variant="secondary" onClick={() => setDialog("import")}>
      Import
    </Button>
  );

  return (
    <section aria-labelledby="set-heading" className="flex flex-col gap-6">
      <BackLink />

      <header className="flex items-start justify-between gap-4 max-md:flex-col">
        <div className="min-w-0">
          {set ? (
            <h1 id="set-heading" className="truncate text-2xl font-semibold text-stone-900">
              {set.name}
            </h1>
          ) : (
            <>
              <h1 id="set-heading" className="sr-only">
                Set
              </h1>
              <Skeleton className="h-8 w-56" />
            </>
          )}
          <p className="mt-1 text-sm text-stone-500" aria-live="polite">
            {wordsQuery.isSuccess ? pluralizeWords(total) : "\u00a0"}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button variant="secondary" onClick={() => setDialog("rename")} disabled={!set}>
            Rename
          </Button>
          <Button variant="secondary" onClick={() => setDialog("delete")} disabled={!set}>
            Delete set
          </Button>
          {importButton}
          {addWordButton}
        </div>
      </header>

      {wordsQuery.isPending && (
        <div className={GRID} aria-busy="true" aria-label="Loading words">
          {Array.from({ length: 12 }, (_, i) => (
            <WordTileSkeleton key={i} />
          ))}
        </div>
      )}

      {wordsQuery.isError && !wordsQuery.data && (
        <ErrorState
          title="Could not load the words"
          message={errorMessage(wordsQuery.error)}
          onRetry={() => wordsQuery.refetch()}
          retrying={wordsQuery.isFetching}
        />
      )}

      {wordsQuery.isSuccess && words.length === 0 && (
        <EmptyState
          title="This set has no words yet"
          description="Add a word, or import a whole list at once."
          action={
            <div className="flex gap-2">
              {importButton}
              {addWordButton}
            </div>
          }
        />
      )}

      {words.length > 0 && (
        <>
          <ul className={GRID}>
            {words.map((word) => (
              <li key={word.id}>
                <WordTile word={word} onOpen={() => openWord(word.id)} />
              </li>
            ))}
          </ul>
          {hasNextPage && (
            <div className="flex flex-col items-center gap-2">
              <Button
                variant="secondary"
                onClick={() => fetchNextPage()}
                pending={isFetchingNextPage}
              >
                Load more
              </Button>
              <p className="text-xs text-stone-500">
                Showing {words.length} of {total}
              </p>
            </div>
          )}
          {wordsQuery.isFetchNextPageError && (
            <p role="alert" className="text-center text-sm text-rose-700">
              Could not load more words. {errorMessage(wordsQuery.error)}
            </p>
          )}
        </>
      )}

      {selectedWord && <WordModal setId={setId} word={selectedWord} onClose={closeWord} />}
      {selectedWordId && !selectedWord && wordsQuery.isSuccess && !searchingForWord && (
        <Dialog open onClose={closeWord} title="Word not found" size="sm">
          <p className="text-sm text-stone-700">
            This word isn't in the set anymore. It may have been removed.
          </p>
        </Dialog>
      )}

      {dialog === "add" && <AddWordDialog setId={setId} onClose={() => setDialog(null)} />}
      {dialog === "import" && (
        <ImportWordsDialog setId={setId} onClose={() => setDialog(null)} />
      )}
      {dialog === "rename" && set && (
        <RenameSetDialog set={set} onClose={() => setDialog(null)} />
      )}
      {dialog === "delete" && set && (
        <DeleteSetDialog
          set={set}
          onClose={() => setDialog(null)}
          onDeleted={() => navigate("/library", { replace: true })}
        />
      )}
    </section>
  );
}

function BackLink() {
  return (
    <Link
      to="/library"
      className="inline-flex w-fit items-center gap-1 rounded text-sm font-medium text-stone-600 hover:text-stone-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700"
    >
      <span aria-hidden="true">←</span> All sets
    </Link>
  );
}
