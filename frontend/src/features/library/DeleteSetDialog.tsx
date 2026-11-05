import { ConfirmDialog } from "../../components/ConfirmDialog";
import { errorMessage, pluralizeWords } from "./format";
import { useDeleteSet } from "./hooks";

interface DeleteSetDialogProps {
  set: { id: string; name: string; word_count?: number };
  onClose: () => void;
  onDeleted?: () => void;
}

export function DeleteSetDialog({ set, onClose, onDeleted }: DeleteSetDialogProps) {
  const deleteSet = useDeleteSet({ onDeleted });
  const words =
    set.word_count === undefined ? "All of its words" : `All ${pluralizeWords(set.word_count)} in it`;

  return (
    <ConfirmDialog
      open
      title="Delete set?"
      message={
        <>
          <p>
            Delete <strong className="font-semibold text-stone-900">“{set.name}”</strong>?
          </p>
          <p className="mt-2">{words} will be removed. This cannot be undone.</p>
        </>
      }
      confirmLabel="Delete set"
      pending={deleteSet.isPending}
      error={
        deleteSet.error
          ? errorMessage(deleteSet.error, "This set no longer exists. The list has been refreshed.")
          : null
      }
      onConfirm={() => deleteSet.mutate(set.id, { onSuccess: onClose })}
      onCancel={onClose}
    />
  );
}
