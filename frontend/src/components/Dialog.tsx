import { useEffect, useId, useRef, type ReactNode, type RefObject } from "react";

type Size = "sm" | "md" | "lg";

const SIZES: Record<Size, string> = {
  sm: "max-w-md",
  md: "max-w-lg",
  lg: "max-w-3xl",
};

/** Main panel width + gap + aside (w-80); below lg the aside stacks under the panel. */
const SIZES_WITH_ASIDE: Record<Size, string> = {
  sm: "max-w-[49rem] max-lg:max-w-md",
  md: "max-w-[53rem] max-lg:max-w-lg",
  lg: "max-w-[69rem] max-lg:max-w-3xl",
};

const CLOSE_BUTTON_CLASS =
  "-mr-2 ml-auto rounded-lg p-2 text-stone-500 hover:bg-stone-100 hover:text-stone-800 focus-visible:outline-2 focus-visible:outline-red-700";

export interface DialogAside {
  title: ReactNode;
  closeLabel?: string;
  onClose: () => void;
  children: ReactNode;
}

export interface DialogProps {
  open: boolean;
  onClose: () => void;
  title: ReactNode;
  /** Visually hide the title (it still labels the dialog for screen readers). */
  hideTitle?: boolean;
  description?: ReactNode;
  size?: Size;
  /** Element to focus when the dialog opens; defaults to the first focusable element. */
  initialFocusRef?: RefObject<HTMLElement | null>;
  children: ReactNode;
  footer?: ReactNode;
  /** Secondary panel shown beside the dialog. Escape closes it before the dialog. */
  aside?: DialogAside;
}

export function Dialog(props: DialogProps) {
  if (!props.open) return null;
  return <OpenDialog {...props} />;
}

/**
 * Native <dialog> opened with showModal(): the browser makes the rest of the page inert
 * (focus stays inside), puts it in the top layer, and fires `cancel` on Escape.
 */
function OpenDialog({
  onClose,
  title,
  hideTitle,
  description,
  size = "md",
  initialFocusRef,
  children,
  footer,
  aside,
}: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const descriptionId = useId();
  const onCloseRef = useRef(onClose);
  const onCloseAsideRef = useRef(aside?.onClose);
  // Only a press that both starts and ends on the backdrop closes the dialog, so dragging
  // a text selection out of an input does not dismiss it.
  const pressStartedOnBackdrop = useRef(false);
  useEffect(() => {
    onCloseRef.current = onClose;
    onCloseAsideRef.current = aside?.onClose;
  }, [onClose, aside?.onClose]);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    const previouslyFocused = document.activeElement as HTMLElement | null;
    dialog.showModal();
    initialFocusRef?.current?.focus();
    return () => {
      dialog.close();
      if (previouslyFocused?.isConnected) previouslyFocused.focus();
    };
  }, [initialFocusRef]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      aria-describedby={description ? descriptionId : undefined}
      onCancel={(event) => {
        event.preventDefault();
        (onCloseAsideRef.current ?? onCloseRef.current)();
      }}
      onMouseDown={(event) => {
        pressStartedOnBackdrop.current = event.target === event.currentTarget;
      }}
      onClick={(event) => {
        if (pressStartedOnBackdrop.current && event.target === event.currentTarget) {
          onCloseRef.current();
        }
        pressStartedOnBackdrop.current = false;
      }}
      className={`m-auto w-full ${aside ? SIZES_WITH_ASIDE[size] : SIZES[size]} max-h-[90vh] overflow-visible bg-transparent p-0 backdrop:bg-stone-950/50 max-md:max-w-[calc(100%-1.5rem)]`}
    >
      <div className="flex max-h-[90vh] items-start gap-4 max-lg:flex-col max-lg:items-stretch max-lg:overflow-y-auto">
        <div className="flex max-h-[90vh] min-w-0 flex-1 flex-col overflow-hidden rounded-2xl bg-white shadow-xl max-lg:shrink-0">
          <div className="flex items-start justify-between gap-4 border-b border-stone-100 px-6 py-4 max-md:px-4">
            <div className={hideTitle ? "sr-only" : "min-w-0"}>
              <h2 id={titleId} className="text-lg font-semibold text-stone-900">
                {title}
              </h2>
              {description && (
                <p id={descriptionId} className="mt-1 text-sm text-stone-600">
                  {description}
                </p>
              )}
            </div>
            <CloseButton label="Close" onClick={() => onCloseRef.current()} />
          </div>
          <div className="min-h-0 flex-1 overflow-y-auto px-6 py-5 max-md:px-4">{children}</div>
          {footer && (
            <div className="flex flex-wrap items-center justify-end gap-2 border-t border-stone-100 px-6 py-4 max-md:px-4">
              {footer}
            </div>
          )}
        </div>
        {aside && <AsidePanel {...aside} />}
      </div>
    </dialog>
  );
}

/** Takes focus when it opens and hands it back to the opener when it closes. */
function AsidePanel({ title, closeLabel = "Close panel", onClose, children }: DialogAside) {
  const ref = useRef<HTMLElement>(null);
  const titleId = useId();

  useEffect(() => {
    const previouslyFocused = document.activeElement as HTMLElement | null;
    ref.current?.focus();
    return () => {
      if (previouslyFocused?.isConnected) previouslyFocused.focus();
    };
  }, []);

  return (
    <section
      ref={ref}
      tabIndex={-1}
      aria-labelledby={titleId}
      className="flex max-h-[90vh] w-80 shrink-0 flex-col overflow-hidden rounded-2xl bg-white shadow-xl outline-none max-lg:w-full"
    >
      <div className="flex items-start justify-between gap-4 border-b border-stone-100 px-5 py-4 max-md:px-4">
        <h3 id={titleId} className="min-w-0 text-lg font-semibold text-stone-900">
          {title}
        </h3>
        <CloseButton label={closeLabel} onClick={onClose} />
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-5 py-4 max-md:px-4">{children}</div>
    </section>
  );
}

function CloseButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} aria-label={label} className={CLOSE_BUTTON_CLASS}>
      <svg viewBox="0 0 20 20" className="size-5" fill="currentColor" aria-hidden="true">
        <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22z" />
      </svg>
    </button>
  );
}
