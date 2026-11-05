import { useState } from "react";
import { Button } from "../../components/Button";
import { EmptyState, ErrorState } from "../../components/States";
import type { FlashcardSetSummary } from "../../types/api";
import { DeleteSetDialog } from "./DeleteSetDialog";
import { errorMessage } from "./format";
import { useSets } from "./hooks";
import { SetCard, SetCardSkeleton } from "./SetCard";
import { CreateSetDialog, RenameSetDialog } from "./SetNameDialog";

const GRID = "grid grid-cols-4 gap-4 max-lg:grid-cols-3 max-md:grid-cols-2 max-sm:grid-cols-1";

export function SetListPage() {
  const setsQuery = useSets();
  const [creating, setCreating] = useState(false);
  const [renaming, setRenaming] = useState<FlashcardSetSummary | null>(null);
  const [deleting, setDeleting] = useState<FlashcardSetSummary | null>(null);

  const newSetButton = <Button onClick={() => setCreating(true)}>New set</Button>;

  return (
    <section aria-labelledby="library-heading">
      <div className="mb-6 flex items-end justify-between gap-4">
        <div>
          <h1 id="library-heading" className="text-2xl font-semibold text-stone-900">
            Library
          </h1>
          <p className="mt-1 text-sm text-stone-500">Your flashcard sets.</p>
        </div>
        {setsQuery.data && setsQuery.data.length > 0 && newSetButton}
      </div>

      {setsQuery.isPending && (
        <div className={GRID} aria-busy="true" aria-label="Loading sets">
          {Array.from({ length: 8 }, (_, i) => (
            <SetCardSkeleton key={i} />
          ))}
        </div>
      )}

      {setsQuery.isError && (
        <ErrorState
          title="Could not load your sets"
          message={errorMessage(setsQuery.error)}
          onRetry={() => setsQuery.refetch()}
          retrying={setsQuery.isFetching}
        />
      )}

      {setsQuery.data?.length === 0 && (
        <EmptyState
          title="No sets yet"
          description="Create a set to start collecting words."
          action={newSetButton}
        />
      )}

      {setsQuery.data && setsQuery.data.length > 0 && (
        <ul className={GRID}>
          {setsQuery.data.map((set) => (
            <li key={set.id}>
              <SetCard
                set={set}
                onRename={() => setRenaming(set)}
                onDelete={() => setDeleting(set)}
              />
            </li>
          ))}
        </ul>
      )}

      {creating && <CreateSetDialog onClose={() => setCreating(false)} />}
      {renaming && <RenameSetDialog set={renaming} onClose={() => setRenaming(null)} />}
      {deleting && <DeleteSetDialog set={deleting} onClose={() => setDeleting(null)} />}
    </section>
  );
}
