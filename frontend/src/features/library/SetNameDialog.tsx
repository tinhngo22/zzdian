import { useId, useRef, useState, type FormEvent } from "react";
import { Button } from "../../components/Button";
import { Dialog } from "../../components/Dialog";
import { TextInput } from "../../components/TextInput";
import { useCreateSet, useRenameSet } from "./hooks";
import { errorMessage, SET_NAME_MAX_LENGTH, validateSetName } from "./format";

interface SetNameDialogProps {
  title: string;
  submitLabel: string;
  initialName?: string;
  pending: boolean;
  apiError: string | null;
  onSubmit: (name: string) => void;
  onClose: () => void;
}

/** Mount it to open it; unmount to close (state resets on every open). */
function SetNameDialog({
  title,
  submitLabel,
  initialName = "",
  pending,
  apiError,
  onSubmit,
  onClose,
}: SetNameDialogProps) {
  const formId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [name, setName] = useState(initialName);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const validation = validateSetName(name);
    setError(validation);
    if (!validation) onSubmit(name.trim());
  };

  return (
    <Dialog
      open
      onClose={pending ? () => {} : onClose}
      title={title}
      size="sm"
      initialFocusRef={inputRef}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={pending}>
            Cancel
          </Button>
          <Button type="submit" form={formId} pending={pending}>
            {submitLabel}
          </Button>
        </>
      }
    >
      <form id={formId} noValidate onSubmit={handleSubmit} className="flex flex-col gap-3">
        <TextInput
          ref={inputRef}
          label="Set name"
          value={name}
          maxLength={SET_NAME_MAX_LENGTH + 20}
          onChange={(e) => {
            setName(e.target.value);
            if (error) setError(null);
          }}
          onFocus={(e) => e.currentTarget.select()}
          error={error}
          hint={`Up to ${SET_NAME_MAX_LENGTH} characters.`}
        />
        {apiError && (
          <p role="alert" className="text-sm text-rose-700">
            {apiError}
          </p>
        )}
      </form>
    </Dialog>
  );
}

export function CreateSetDialog({ onClose }: { onClose: () => void }) {
  const createSet = useCreateSet();
  return (
    <SetNameDialog
      title="New set"
      submitLabel="Create set"
      pending={createSet.isPending}
      apiError={createSet.error ? errorMessage(createSet.error) : null}
      onSubmit={(name) => createSet.mutate(name, { onSuccess: onClose })}
      onClose={onClose}
    />
  );
}

export function RenameSetDialog({
  set,
  onClose,
}: {
  set: { id: string; name: string };
  onClose: () => void;
}) {
  const renameSet = useRenameSet();
  return (
    <SetNameDialog
      title="Rename set"
      submitLabel="Save"
      initialName={set.name}
      pending={renameSet.isPending}
      apiError={
        renameSet.error
          ? errorMessage(renameSet.error, "This set no longer exists. The list has been refreshed.")
          : null
      }
      onSubmit={(name) =>
        name === set.name
          ? onClose()
          : renameSet.mutate({ setId: set.id, name }, { onSuccess: onClose })
      }
      onClose={onClose}
    />
  );
}
