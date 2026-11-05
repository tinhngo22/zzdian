import type { MouseEvent, ReactNode } from "react";
import { Link } from "react-router";
import { Card } from "../../components/Card";
import { Skeleton } from "../../components/Spinner";
import type { FlashcardSetSummary } from "../../types/api";
import { pluralizeWords } from "./format";

interface SetCardProps {
  set: FlashcardSetSummary;
  onRename: () => void;
  onDelete: () => void;
}

export function SetCard({ set, onRename, onDelete }: SetCardProps) {
  // The link's ::after covers the whole card so the card is clickable, while the action
  // buttons sit above it (z-10) instead of being nested inside the link.
  return (
    <Card className="group relative flex h-full min-h-32 flex-col justify-between p-5 transition-shadow hover:shadow-md has-[a:focus-visible]:outline-2 has-[a:focus-visible]:outline-offset-2 has-[a:focus-visible]:outline-red-700">
      <div className="min-w-0 pr-16">
        <h2 className="truncate text-base font-semibold text-stone-900" title={set.name}>
          <Link
            to={`/library/${set.id}`}
            className="outline-none after:absolute after:inset-0 after:rounded-xl"
          >
            {set.name}
          </Link>
        </h2>
        <p className="mt-1 text-sm text-stone-500">{pluralizeWords(set.word_count)}</p>
      </div>
      <div className="absolute top-3 right-3 z-10 flex gap-1 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100 max-lg:opacity-100">
        <IconButton label={`Rename ${set.name}`} onClick={onRename}>
          <path d="M13.586 3.586a2 2 0 1 1 2.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793 3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
        </IconButton>
        <IconButton label={`Delete ${set.name}`} onClick={onDelete} danger>
          <path
            fillRule="evenodd"
            d="M9 2a1 1 0 0 0-.894.553L7.382 4H4a1 1 0 0 0 0 2v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V6a1 1 0 1 0 0-2h-3.382l-.724-1.447A1 1 0 0 0 11 2H9zM7 8a1 1 0 0 1 2 0v6a1 1 0 1 1-2 0V8zm5-1a1 1 0 0 0-1 1v6a1 1 0 1 0 2 0V8a1 1 0 0 0-1-1z"
            clipRule="evenodd"
          />
        </IconButton>
      </div>
    </Card>
  );
}

function IconButton({
  label,
  onClick,
  danger,
  children,
}: {
  label: string;
  onClick: () => void;
  danger?: boolean;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      onClick={(event: MouseEvent) => {
        event.stopPropagation();
        event.preventDefault();
        onClick();
      }}
      className={`rounded-lg p-1.5 text-stone-500 hover:bg-stone-100 focus-visible:outline-2 focus-visible:outline-red-700 ${
        danger ? "hover:text-rose-700" : "hover:text-stone-900"
      }`}
    >
      <svg viewBox="0 0 20 20" fill="currentColor" className="size-4" aria-hidden="true">
        {children}
      </svg>
    </button>
  );
}

export function SetCardSkeleton() {
  return (
    <Card className="flex min-h-32 flex-col gap-3 p-5">
      <Skeleton className="h-5 w-2/3" />
      <Skeleton className="h-4 w-1/4" />
    </Card>
  );
}
