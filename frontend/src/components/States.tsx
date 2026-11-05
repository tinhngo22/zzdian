import type { ReactNode } from "react";
import { Button } from "./Button";
import { Spinner } from "./Spinner";

export function PageSpinner({ label = "Loading" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-3 py-24 text-stone-500">
      <Spinner className="size-6" />
      <span>{label}…</span>
    </div>
  );
}

export function InlineSpinner({ label = "Loading" }: { label?: string }) {
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm text-stone-500">
      <Spinner />
      <span>{label}…</span>
    </span>
  );
}

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  retrying?: boolean;
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  retrying,
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-3 rounded-xl border border-rose-200 bg-rose-50 px-6 py-10 text-center"
    >
      <p className="font-semibold text-rose-900">{title}</p>
      <p className="text-sm text-rose-800">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" onClick={onRetry} pending={retrying}>
          Try again
        </Button>
      )}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-stone-300 bg-white px-6 py-16 text-center">
      <p className="text-lg font-semibold text-stone-800">{title}</p>
      {description && <p className="text-sm text-stone-500">{description}</p>}
      {action}
    </div>
  );
}
