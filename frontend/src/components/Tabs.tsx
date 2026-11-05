import { useId, useRef, type KeyboardEvent, type ReactNode } from "react";

export interface TabItem {
  id: string;
  label: ReactNode;
  /** Accessible name when the label alone is not descriptive (e.g. a single glyph). */
  ariaLabel?: string;
  labelClassName?: string;
}

interface TabsProps {
  items: TabItem[];
  selectedId: string;
  onSelect: (id: string) => void;
  label: string;
  /** Rendered after the tabs inside the strip (e.g. a loading spinner). */
  trailing?: ReactNode;
  children: ReactNode;
}

/** WAI-ARIA tabs: arrow keys / Home / End move between tabs; only the active tab is in the tab order. */
export function Tabs({ items, selectedId, onSelect, label, trailing, children }: TabsProps) {
  const baseId = useId();
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  const focusTab = (index: number) => {
    const item = items[(index + items.length) % items.length];
    onSelect(item.id);
    tabRefs.current[item.id]?.focus();
  };

  const onKeyDown = (event: KeyboardEvent, index: number) => {
    const moves: Record<string, number> = {
      ArrowRight: index + 1,
      ArrowLeft: index - 1,
      Home: 0,
      End: items.length - 1,
    };
    if (event.key in moves) {
      event.preventDefault();
      focusTab(moves[event.key]);
    }
  };

  return (
    <div className="flex flex-col">
      <div className="flex items-center gap-2 overflow-x-auto border-b border-stone-200">
        <div role="tablist" aria-label={label} className="flex gap-1">
          {items.map((item, index) => {
            const selected = item.id === selectedId;
            return (
              <button
                key={item.id}
                ref={(el) => {
                  tabRefs.current[item.id] = el;
                }}
                id={`${baseId}-tab-${item.id}`}
                type="button"
                role="tab"
                aria-selected={selected}
                aria-controls={`${baseId}-panel`}
                aria-label={item.ariaLabel}
                tabIndex={selected ? 0 : -1}
                onClick={() => onSelect(item.id)}
                onKeyDown={(event) => onKeyDown(event, index)}
                className={`-mb-px shrink-0 border-b-2 px-3 py-2 text-sm font-medium whitespace-nowrap focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-red-700 ${
                  selected
                    ? "border-red-700 text-red-800"
                    : "border-transparent text-stone-600 hover:border-stone-300 hover:text-stone-900"
                } ${item.labelClassName ?? ""}`}
              >
                {item.label}
              </button>
            );
          })}
        </div>
        {trailing}
      </div>
      <div
        id={`${baseId}-panel`}
        role="tabpanel"
        aria-labelledby={`${baseId}-tab-${selectedId}`}
        tabIndex={0}
        className="pt-5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700"
      >
        {children}
      </div>
    </div>
  );
}
