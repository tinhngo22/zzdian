import { Skeleton } from "../../components/Spinner";
import type { SetWord } from "../../types/api";

export function WordTile({ word, onOpen }: { word: SetWord; onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      data-word-id={word.id}
      aria-label={`${word.simplified}${word.pinyin ? `, ${word.pinyin}` : ""}`}
      className="flex aspect-[4/3] w-full flex-col items-center justify-center gap-1 rounded-xl border border-stone-200 bg-white px-3 shadow-sm transition hover:-translate-y-0.5 hover:border-red-200 hover:shadow-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-700"
    >
      <span
        lang="zh-Hans"
        className="max-w-full truncate font-cjk text-4xl leading-tight text-stone-900 max-md:text-3xl"
      >
        {word.simplified}
      </span>
      <span className="max-w-full truncate text-sm text-stone-500">
        {word.pinyin?.trim() || <span className="text-stone-300">—</span>}
      </span>
    </button>
  );
}

export function WordTileSkeleton() {
  return (
    <div className="flex aspect-[4/3] flex-col items-center justify-center gap-2 rounded-xl border border-stone-200 bg-white">
      <Skeleton className="h-9 w-16" />
      <Skeleton className="h-4 w-12" />
    </div>
  );
}
