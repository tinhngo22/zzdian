import { useId, type InputHTMLAttributes, type Ref, type TextareaHTMLAttributes } from "react";

const FIELD =
  "w-full rounded-lg border bg-white px-3 py-2 text-stone-900 placeholder:text-stone-400 focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-red-700";

interface FieldShellProps {
  id: string;
  label: string;
  hint?: string;
  error?: string | null;
  optional?: boolean;
  children: React.ReactNode;
}

function FieldShell({ id, label, hint, error, optional, children }: FieldShellProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-sm font-medium text-stone-700">
        {label}
        {optional && <span className="ml-1 font-normal text-stone-400">(optional)</span>}
      </label>
      {children}
      {hint && !error && (
        <p id={`${id}-hint`} className="text-xs text-stone-500">
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} role="alert" className="text-sm text-rose-700">
          {error}
        </p>
      )}
    </div>
  );
}

function describedBy(id: string, hint?: string, error?: string | null) {
  if (error) return `${id}-error`;
  if (hint) return `${id}-hint`;
  return undefined;
}

interface TextInputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "id"> {
  label: string;
  hint?: string;
  error?: string | null;
  optional?: boolean;
  ref?: Ref<HTMLInputElement>;
}

export function TextInput({ label, hint, error, optional, className = "", ...rest }: TextInputProps) {
  const id = useId();
  return (
    <FieldShell id={id} label={label} hint={hint} error={error} optional={optional}>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        className={`${FIELD} h-10 ${error ? "border-rose-500" : "border-stone-300"} ${className}`}
        {...rest}
      />
    </FieldShell>
  );
}

interface TextAreaProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "id"> {
  label: string;
  hint?: string;
  error?: string | null;
  optional?: boolean;
  ref?: Ref<HTMLTextAreaElement>;
}

export function TextArea({ label, hint, error, optional, className = "", ...rest }: TextAreaProps) {
  const id = useId();
  return (
    <FieldShell id={id} label={label} hint={hint} error={error} optional={optional}>
      <textarea
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, hint, error)}
        className={`${FIELD} resize-y ${error ? "border-rose-500" : "border-stone-300"} ${className}`}
        {...rest}
      />
    </FieldShell>
  );
}
