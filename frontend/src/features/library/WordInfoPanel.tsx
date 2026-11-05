import type { ReactNode } from "react";
import type { SetWord } from "../../types/api";
// import { formatDate } from "./format";

export function WordInfoPanel({ word }: { word: SetWord }) {
  const rows: { label: string; value: ReactNode }[] = [];
  const add = (label: string, value: string | null | undefined, render?: (v: string) => ReactNode) => {
    const trimmed = value?.trim();
    if (trimmed) rows.push({ label, value: render ? render(trimmed) : trimmed });
  };

  add("Simplified", word.simplified, (v) => (
    <span lang="zh-Hans" className="font-cjk text-2xl">
      {v}
    </span>
  ));
  add("Traditional", word.traditional, (v) => (
    <span lang="zh-Hant" className="font-cjk text-2xl">
      {v}
    </span>
  ));
  add("Pinyin", word.pinyin);
  add("Definitions", word.definitions, (v) => <span className="whitespace-pre-line">{v}</span>);
  // add("Added", word.added_at, formatDate);

  return (
    <dl className="grid grid-cols-[8rem_1fr] gap-x-6 gap-y-4 max-md:grid-cols-1 max-md:gap-y-1">
      {rows.map((row) => (
        <div key={row.label} className="contents">
          <dt className="pt-0.5 text-sm font-medium text-stone-500 max-md:pt-3">{row.label}</dt>
          <dd className="text-stone-900">{row.value}</dd>
        </div>
      ))}
    </dl>
  );
}
