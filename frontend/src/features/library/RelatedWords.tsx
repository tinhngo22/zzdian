import { useId, useState } from "react";
import { InlineSpinner } from "../../components/States";
import { Button } from "../../components/Button";
import { errorMessage } from "./format";
import { useWordsByCharacter, useWordsByComponent } from "./hooks";

interface RelatedWordsProps {
  /** "character": words containing it; "component": words with a character built from it. */
  by: "character" | "component";
  /** characters.id of the character or component. */
  id: number;
  glyph: string;
  /** The word the modal is showing; it is left out of the list. */
  currentSimplified: string;
}

/** Collapsed by default; the request is only made once the user expands it. */
export function RelatedWords({ by, id, glyph, currentSimplified }: RelatedWordsProps) {
  const [open, setOpen] = useState(false);
  const panelId = useId();
  const byCharacter = useWordsByCharacter(id, open && by === "character");
  const byComponent = useWordsByComponent(id, open && by === "component");
  const query = by === "character" ? byCharacter : byComponent;
  const words = query.data?.words.filter((w) => w.simplified !== currentSimplified) ?? [];

  return (
    <div className="rounded-xl border border-stone-200">
      <button
        type="button"
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-2 rounded-xl px-4 py-3 text-left text-sm font-medium text-stone-800 hover:bg-stone-50 focus-visible:outline-2 focus-visible:outline-red-700"
      >
        <span>
          Words with <span lang="zh-Hans" className="font-cjk">{glyph}</span>
        </span>
        <svg
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
          className={`size-4 text-stone-500 transition-transform ${open ? "rotate-180" : ""}`}
        >
          <path
            fillRule="evenodd"
            d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 11.17l3.71-3.94a.75.75 0 1 1 1.08 1.04l-4.25 4.5a.75.75 0 0 1-1.08 0l-4.25-4.5a.75.75 0 0 1 .02-1.06z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {open && (
        <div id={panelId} className="border-t border-stone-200 px-4 py-3">
          {query.isPending && <InlineSpinner label="Finding related words" />}
          {query.isError && (
            <div role="alert" className="flex items-center gap-3 text-sm text-rose-700">
              <span>
                {errorMessage(query.error, by === "character" ? "Character not found." : "Component not found.")}
              </span>
              <Button size="sm" variant="ghost" onClick={() => query.refetch()}>
                Retry
              </Button>
            </div>
          )}
          {query.isSuccess && words.length === 0 && (
            <p className="text-sm text-stone-500">
              No other saved words {by === "character" ? "contain" : "use the component"}{" "}
              <span lang="zh-Hans" className="font-cjk">{glyph}</span>.
            </p>
          )}
          {words.length > 0 && (
            <ul className="divide-y divide-stone-100">
              {words.map((w) => (
                <li key={w.id} className="flex items-baseline gap-3 py-2">
                  <span lang="zh-Hans" className="font-cjk text-lg text-stone-900">
                    {w.simplified}
                  </span>
                  {w.pinyin && <span className="text-sm text-stone-500">{w.pinyin}</span>}
                  {w.definitions && (
                    <span className="ml-auto max-w-[50%] truncate text-sm text-stone-500" title={w.definitions}>
                      {w.definitions.split("\n")[0]}
                    </span>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
